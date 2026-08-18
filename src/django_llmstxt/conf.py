from __future__ import annotations

from typing import Any

from django.conf import settings
from django.utils.module_loading import import_string

DEFAULTS: dict[str, Any] = {
    # Site-wide metadata used as the header of llms.txt / llms-full.txt.
    # Views may override per-view via attributes.
    "SITE_TITLE": "",
    "SITE_DESCRIPTION": "",
    # Route-path globs (not file paths). Exclude wins over include, and wins
    # over every other surface: no .md conversion, no index entry.
    "INCLUDE": ["*"],
    "EXCLUDE": [],
    # Emit the llms.txt v2 discovery relations as a Link: response header
    # (rel="alternate" for the .md twin, rel="describedby" for llms.txt).
    "LINK_HEADERS": True,
    # Callable (or dotted path to one) turning an HTML document into markdown:
    #   converter(html: str, *, url: str = "") -> str
    "CONVERTER": "django_llmstxt.convert.html_to_markdown",
}


class AppSettings:
    """
    Lazy access to the ``LLMSTXT`` settings dict, falling back to DEFAULTS.

    Read at call time so ``override_settings`` works in tests.
    """

    def __getattr__(self, name: str) -> Any:
        if name not in DEFAULTS:
            msg = f"Unknown LLMSTXT setting: {name!r}"
            raise AttributeError(msg)
        user_settings = getattr(settings, "LLMSTXT", {})
        value = user_settings.get(name, DEFAULTS[name])
        if name == "CONVERTER" and isinstance(value, str):
            value = import_string(value)
        return value


app_settings = AppSettings()
