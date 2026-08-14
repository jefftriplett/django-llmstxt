from __future__ import annotations

import fnmatch
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from django_llmstxt.conf import app_settings


@dataclass
class LlmsEntry:
    """A single page listed in llms.txt / llms-full.txt."""

    title: str
    url: str
    description: str = ""
    # None means "index only": listed in llms.txt, no body in llms-full.txt.
    content: str | None = None


class LlmsSection:
    """
    A group of pages, declared the way django.contrib.sitemaps declares
    URL sets and django.contrib.syndication declares feeds.

    Subclass and override ``items()`` plus the ``item_*`` hooks, or return
    plain dicts / LlmsEntry instances from ``items()`` for static pages.

    ``title = None`` means the entries render ungrouped, before any
    ``## Heading`` sections — typically used for root-level pages.
    """

    title: str | None = None
    description: str | None = None

    def items(self) -> Iterable[Any]:
        return []

    def item_title(self, item: Any) -> str:
        if isinstance(item, LlmsEntry):
            return item.title
        if isinstance(item, dict):
            return str(item["title"])
        return str(item)

    def item_url(self, item: Any) -> str:
        if isinstance(item, LlmsEntry):
            return item.url
        if isinstance(item, dict):
            return str(item["url"])
        if isinstance(item, str):
            return item
        get_absolute_url = getattr(item, "get_absolute_url", None)
        if get_absolute_url is not None:
            return str(get_absolute_url())
        msg = f"Cannot determine URL for {item!r}: implement item_url()"
        raise TypeError(msg)

    def item_description(self, item: Any) -> str:
        if isinstance(item, LlmsEntry):
            return item.description
        if isinstance(item, dict):
            return str(item.get("description", ""))
        return ""

    def item_content(self, item: Any) -> str | None:
        if isinstance(item, LlmsEntry):
            return item.content
        if isinstance(item, dict):
            return item.get("content")
        return None

    def get_entries(self) -> list[LlmsEntry]:
        entries = []
        for item in self.items():
            entry = LlmsEntry(
                title=self.item_title(item),
                url=self.item_url(item),
                description=self.item_description(item),
                content=self.item_content(item),
            )
            if path_allowed(entry.url):
                entries.append(entry)
        return entries


def path_allowed(path: str) -> bool:
    """EXCLUDE wins over INCLUDE; globs match against the route path."""
    includes = app_settings.INCLUDE
    excludes = app_settings.EXCLUDE
    if includes and not any(fnmatch.fnmatchcase(path, glob) for glob in includes):
        return False
    return not any(fnmatch.fnmatchcase(path, glob) for glob in excludes)
