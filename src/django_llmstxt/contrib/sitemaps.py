from __future__ import annotations

from typing import Any

from django.contrib.sitemaps import Sitemap

from django_llmstxt.sections import LlmsSection


class SitemapSection(LlmsSection):
    """
    llms.txt section that reuses an existing
    ``django.contrib.sitemaps.Sitemap``.

    Point it at a Sitemap class or instance and its ``items()`` become the
    section's entries, each located exactly where the sitemap already
    locates it (a ``location`` attribute, a ``location()`` method, or the
    item's ``get_absolute_url()``). The two surfaces stay in lockstep::

        from myblog.sitemaps import BlogSitemap

        path(
            "llms.txt",
            LlmsTxtView.as_view(
                sections={"blog": SitemapSection(BlogSitemap, title="Blog")}
            ),
        )

    Sitemaps carry no titles, so ``item_title`` falls back to ``str(item)``
    — give your model a readable ``__str__`` or override ``item_title`` for
    nicer labels. Entries are metadata-only (``item_content`` returns
    ``None``); subclass and override it to publish bodies in
    ``llms-full.txt``.
    """

    def __init__(
        self, sitemap: type[Sitemap[Any]] | Sitemap[Any], *, title: str | None = None
    ) -> None:
        self.sitemap = sitemap() if isinstance(sitemap, type) else sitemap
        if title is not None:
            self.title = title

    def items(self) -> list[Any]:
        return list(self.sitemap.items())

    def item_url(self, item: Any) -> str:
        # Resolve the sitemap's location the way it publishes it: a
        # location() method (the default returns item.get_absolute_url()) or
        # a plain location attribute. Either way the two surfaces never drift.
        location: Any = self.sitemap.location
        if callable(location):
            return str(location(item))
        return str(location)
