from __future__ import annotations

from django.urls import Resolver404, resolve

MARKDOWN_MEDIA_TYPES = frozenset({"text/markdown", "text/x-markdown"})


def accepts_markdown(accept_header: str) -> bool:
    """
    True when the Accept header allows text/markdown with q > 0.

    Deliberately ignores q-value *ordering* — an agent that sends
    ``text/markdown`` alongside ``text/html`` is opting in.
    """
    for part in accept_header.split(","):
        token = part.strip()
        if not token:
            continue
        media_type, *params = token.split(";")
        if media_type.strip().lower() not in MARKDOWN_MEDIA_TYPES:
            continue
        quality = 1.0
        for param in params:
            key, _, value = param.strip().partition("=")
            if key.strip() == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 1.0
        if quality > 0:
            return True
    return False


def markdown_url(path: str) -> str:
    """
    The URL of the markdown twin of ``path``, per the llms.txt v2 spec.

    A path that names a file gets ``.md`` appended (``/page.html`` ->
    ``/page.html.md``). A path without a file name gets ``index.md``
    (``/docs/`` -> ``/docs/index.md``).
    """
    if path.endswith("/"):
        return f"{path}index.md"
    return f"{path}.md"


def markdown_candidates(path: str) -> list[str]:
    """
    The canonical routes that a ``.md`` request may refer to, most specific
    first.

    The v2 spec allows both an appended suffix (``/page.html.md``) and a
    replaced extension (``/page.md``), plus ``index.md`` and
    ``index.html.md`` for paths without a file name.
    """
    canonical = path.removesuffix(".md")
    candidates = [canonical, f"{canonical}/"]
    # /docs/index.md and /index.md name the directory itself.
    if canonical.endswith("/index"):
        candidates.append(canonical.removesuffix("index"))
    # Extension replacement: /page.md may stand for /page.html.
    if "." not in canonical.rsplit("/", 1)[-1]:
        candidates.append(f"{canonical}.html")
    return candidates


def llms_txt_url(path: str) -> str | None:
    """
    The URL of the llms.txt file that covers ``path``, or None.

    An llms.txt file covers the pages under its own path, so this walks up
    from ``path`` and returns the most specific file that the URLconf
    resolves.
    """
    prefix = path if path.endswith("/") else f"{path.rsplit('/', 1)[0]}/"
    while True:
        candidate = f"{prefix}llms.txt"
        try:
            resolve(candidate)
        except Resolver404:
            pass
        else:
            return candidate
        if prefix == "/":
            return None
        prefix = f"{prefix[:-1].rsplit('/', 1)[0]}/"


def build_link_header(*, alternate: str = "", describedby: str = "") -> str:
    """Render a ``Link:`` header value for the v2 discovery relations."""
    links = []
    if alternate:
        links.append(f'<{alternate}>; rel="alternate"; type="text/markdown"')
    if describedby:
        links.append(f'<{describedby}>; rel="describedby"')
    return ", ".join(links)
