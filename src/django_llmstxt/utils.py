from __future__ import annotations

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
