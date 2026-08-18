from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.urls import Resolver404, resolve
from django.utils.cache import patch_cache_control, patch_vary_headers

from django_llmstxt.conf import app_settings
from django_llmstxt.sections import path_allowed
from django_llmstxt.utils import (
    accepts_markdown,
    build_link_header,
    llms_txt_url,
    markdown_candidates,
    markdown_url,
)
from django_llmstxt.views import MARKDOWN_CONTENT_TYPE


class MarkdownDetails:
    """
    Attached to every request as ``request.markdown`` by
    :class:`LlmsMarkdownMiddleware`.

    Truthy when the request opted into a markdown representation, via either
    a ``.md`` URL suffix or ``Accept: text/markdown`` negotiation::

        if request.markdown:
            # this request will be served markdown
            ...

        if request.markdown.via_accept:
            # opted in through content negotiation, not a .md twin
            ...
    """

    __slots__ = ("via_accept", "via_suffix")

    def __init__(self) -> None:
        self.via_accept = False
        self.via_suffix = False

    def __bool__(self) -> bool:
        return self.via_accept or self.via_suffix

    def __repr__(self) -> str:
        return (
            f"<MarkdownDetails via_accept={self.via_accept} "
            f"via_suffix={self.via_suffix}>"
        )


class LlmsMarkdownMiddleware:
    """
    Serves markdown representations of ordinary HTML pages:

    - ``/<route>.md`` — rewrites the request to the canonical route and
      converts the HTML response to markdown.
    - ``Accept: text/markdown`` — same conversion, negotiated on the
      canonical URL, with ``Vary: Accept`` set.

    A view opts out of HTML conversion (or supplies hand-written markdown)
    by setting an ``llms_md`` attribute — on the response, on a function
    view, or on a CBV class. A string is served verbatim; a callable is
    called with the request.

    Responses rendered for an authenticated user are sent with
    ``Cache-Control: private, no-store``.
    """

    sync_capable = True
    async_capable = True

    def __init__(
        self,
        get_response: (
            Callable[[HttpRequest], HttpResponseBase]
            | Callable[[HttpRequest], Awaitable[HttpResponseBase]]
        ),
    ) -> None:
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)

        if self.async_mode:
            # Mark the class as async-capable, but do the actual switch
            # inside __call__ to avoid swapping out dunder methods
            markcoroutinefunction(self)

    def __call__(
        self, request: HttpRequest
    ) -> HttpResponseBase | Awaitable[HttpResponseBase]:
        self.process_request(request)
        if self.async_mode:
            return self.__acall__(request)
        response = cast(HttpResponseBase, self.get_response(request))
        return self.process_response(request, response)

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        response = await self.get_response(request)  # type: ignore [misc]
        return self.process_response(request, response)

    def process_request(self, request: HttpRequest) -> None:
        markdown = MarkdownDetails()
        request.markdown = markdown  # type: ignore [attr-defined]

        if accepts_markdown(request.headers.get("Accept", "")):
            markdown.via_accept = True

        path = request.path_info
        if request.method not in ("GET", "HEAD") or not path.endswith(".md"):
            return

        # An exact match means the project owns this route — a static .md
        # file or a custom .md view. Existing surfaces win.
        try:
            resolve(path)
            return
        except Resolver404:
            pass

        for candidate in markdown_candidates(path):
            try:
                resolve(candidate)
            except Resolver404:
                continue
            self.rewrite_path(request, candidate)
            return

        canonical = path.removesuffix(".md")

        # No candidate resolves: a fallback middleware (e.g. flatpages, whose
        # URLs always end in "/") may still serve the canonical path, so
        # rewrite and mark regardless. A plain 404 response is passed
        # through by process_response.
        if canonical.endswith("/"):
            self.rewrite_path(request, canonical)
        else:
            self.rewrite_path(request, f"{canonical}/")

    def rewrite_path(self, request: HttpRequest, path: str) -> None:
        # request.path is materialized at request creation (it is what
        # FlatpageFallbackMiddleware reads), so update it alongside path_info,
        # preserving any script-name prefix.
        prefix = ""
        if request.path.endswith(request.path_info):
            prefix = request.path[: -len(request.path_info)]
        request.path_info = path
        request.path = prefix + path
        request.markdown.via_suffix = True  # type: ignore [attr-defined]

    def process_response(
        self, request: HttpRequest, response: HttpResponseBase
    ) -> HttpResponseBase:
        details: MarkdownDetails | None = getattr(request, "markdown", None)
        if details is None:
            return response
        if response.status_code != 200:
            return response
        if getattr(response, "streaming", False):
            return response
        if "text/html" not in response.headers.get("Content-Type", ""):
            return response
        if not path_allowed(request.path_info):
            return response

        if not details:
            # An ordinary HTML response, but this URL also answers to
            # Accept: text/markdown, so a shared cache must keep the two
            # representations apart.
            patch_vary_headers(response, ["Accept"])
            # Advertise the markdown twin and the covering llms.txt file,
            # as the v2 spec recommends.
            self.add_link_header(request, response, alternate=True)
            return response

        markdown = self.get_markdown_override(request, response)
        if markdown is None:
            converter = app_settings.CONVERTER
            html = cast(HttpResponse, response).text
            markdown = converter(html, url=request.build_absolute_uri())

        markdown_response = HttpResponse(markdown, content_type=MARKDOWN_CONTENT_TYPE)
        self.add_link_header(request, markdown_response, alternate=False)
        if details.via_accept:
            patch_vary_headers(markdown_response, ["Accept"])
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            patch_cache_control(markdown_response, private=True, no_store=True)
        return markdown_response

    def add_link_header(
        self, request: HttpRequest, response: HttpResponseBase, *, alternate: bool
    ) -> None:
        """
        Add the llms.txt v2 discovery relations to ``response``.

        ``rel="alternate"`` points at the markdown twin of an HTML page, and
        ``rel="describedby"`` at the llms.txt file that covers the path. A
        markdown response is its own alternate, so it gets the second only.
        """
        if not app_settings.LINK_HEADERS:
            return
        # Routes resolve against path_info, but the links a client follows
        # need any script-name prefix back in front.
        path = request.path_info
        prefix = request.path.removesuffix(path) if request.path.endswith(path) else ""
        covering = llms_txt_url(path)
        value = build_link_header(
            alternate=f"{prefix}{markdown_url(path)}" if alternate else "",
            describedby=f"{prefix}{covering}" if covering else "",
        )
        if not value:
            return
        existing = response.headers.get("Link")
        response.headers["Link"] = f"{existing}, {value}" if existing else value

    def get_markdown_override(
        self, request: HttpRequest, response: HttpResponseBase
    ) -> str | None:
        override: Any = getattr(response, "llms_md", None)
        if override is None:
            override = self.get_view_override(request)
        if override is None:
            return None
        if callable(override):
            return override(request)  # type: ignore [no-any-return]
        return str(override)

    def get_view_override(self, request: HttpRequest) -> Any:
        resolver_match = getattr(request, "resolver_match", None)
        if resolver_match is None:
            return None
        callback = resolver_match.func
        view_class = getattr(callback, "view_class", None)
        if view_class is not None:
            return getattr(view_class, "llms_md", None)
        return getattr(callback, "llms_md", None)
