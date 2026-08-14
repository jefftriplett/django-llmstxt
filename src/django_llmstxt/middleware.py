from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.urls import Resolver404, resolve
from django.utils.cache import patch_cache_control, patch_vary_headers

from django_llmstxt.conf import app_settings
from django_llmstxt.sections import path_allowed
from django_llmstxt.utils import accepts_markdown
from django_llmstxt.views import MARKDOWN_CONTENT_TYPE


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
        response = self.get_response(request)
        return self.process_response(request, response)

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        response = await self.get_response(request)  # type: ignore [no-any-return, misc]
        return self.process_response(request, response)

    def process_request(self, request: HttpRequest) -> None:
        request.llms_wants_markdown = False  # type: ignore [attr-defined]
        request.llms_via_accept = False  # type: ignore [attr-defined]

        if accepts_markdown(request.headers.get("Accept", "")):
            request.llms_wants_markdown = True  # type: ignore [attr-defined]
            request.llms_via_accept = True  # type: ignore [attr-defined]

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

        canonical = path.removesuffix(".md")
        for candidate in (canonical, f"{canonical}/"):
            try:
                resolve(candidate)
            except Resolver404:
                continue
            self.rewrite_path(request, candidate)
            return

        # Neither resolves: a fallback middleware (e.g. flatpages, whose
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
        request.llms_wants_markdown = True  # type: ignore [attr-defined]

    def process_response(
        self, request: HttpRequest, response: HttpResponseBase
    ) -> HttpResponseBase:
        if not getattr(request, "llms_wants_markdown", False):
            return response
        if response.status_code != 200:
            return response
        if getattr(response, "streaming", False):
            return response
        if "text/html" not in response.headers.get("Content-Type", ""):
            return response
        if not path_allowed(request.path_info):
            return response

        markdown = self.get_markdown_override(request, response)
        if markdown is None:
            converter = app_settings.CONVERTER
            markdown = converter(response.text, url=request.build_absolute_uri())

        markdown_response = HttpResponse(markdown, content_type=MARKDOWN_CONTENT_TYPE)
        if request.llms_via_accept:  # type: ignore [attr-defined]
            patch_vary_headers(markdown_response, ["Accept"])
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            patch_cache_control(markdown_response, private=True, no_store=True)
        return markdown_response

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
