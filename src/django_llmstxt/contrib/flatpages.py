from __future__ import annotations

from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.db.models import QuerySet

from django_llmstxt.conf import app_settings
from django_llmstxt.sections import LlmsSection


class FlatPagesSection(LlmsSection):
    """
    llms.txt section over ``django.contrib.flatpages``.

    Requires ``"django.contrib.sites"`` and ``"django.contrib.flatpages"`` in
    ``INSTALLED_APPS``. Only pages assigned to the current site are listed
    (same scope as ``FlatpageFallbackMiddleware``). FlatPage content is HTML,
    so it is run through the configured ``LLMSTXT["CONVERTER"]`` for
    ``llms-full.txt``; set ``include_content = False`` to list pages
    metadata-only.
    """

    title = "Pages"
    include_content = True

    def get_queryset(self) -> QuerySet[FlatPage]:
        # Scoped to the current site, matching FlatpageFallbackMiddleware and
        # FlatPageSitemap, so the indexes never list pages their .md twins
        # (or the site itself) would not serve.
        return FlatPage.objects.filter(sites=Site.objects.get_current()).order_by("url")

    def items(self) -> QuerySet[FlatPage]:
        return self.get_queryset()

    def item_title(self, item: FlatPage) -> str:
        return item.title

    def item_url(self, item: FlatPage) -> str:
        return item.get_absolute_url()

    def item_content(self, item: FlatPage) -> str | None:
        if not self.include_content:
            return None
        converter = app_settings.CONVERTER
        markdown: str = converter(item.content, url=item.get_absolute_url())
        return markdown


class FlatPagesIndexSection(FlatPagesSection):
    """Flat pages listed in both indexes, but with no bodies in llms-full.txt."""

    include_content = False
