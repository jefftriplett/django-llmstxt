from __future__ import annotations

from django.contrib.sitemaps import Sitemap

from django_llmstxt.contrib.sitemaps import SitemapSection


class Thing:
    def __init__(self, name: str, url: str) -> None:
        self.name = name
        self._url = url

    def get_absolute_url(self) -> str:
        return self._url

    def __str__(self) -> str:
        return self.name


class ThingSitemap(Sitemap):
    def items(self):
        return [Thing("Alpha", "/alpha/"), Thing("Beta", "/beta/")]


class CustomLocationSitemap(Sitemap):
    """A sitemap whose location() does not use get_absolute_url()."""

    def items(self):
        return ["one", "two"]

    def location(self, item):
        return f"/items/{item}/"


class TestSitemapSection:
    def test_entries_track_the_sitemap(self):
        section = SitemapSection(ThingSitemap, title="Things")
        entries = section.get_entries()
        assert section.get_title() == "Things"
        assert [e.url for e in entries] == ["/alpha/", "/beta/"]
        assert [e.title for e in entries] == ["Alpha", "Beta"]

    def test_entries_are_metadata_only_by_default(self):
        entries = SitemapSection(ThingSitemap).get_entries()
        assert all(e.content is None for e in entries)

    def test_accepts_an_instance(self):
        entries = SitemapSection(ThingSitemap(), title="Things").get_entries()
        assert [e.url for e in entries] == ["/alpha/", "/beta/"]

    def test_respects_a_custom_location_method(self):
        entries = SitemapSection(CustomLocationSitemap).get_entries()
        assert [e.url for e in entries] == ["/items/one/", "/items/two/"]

    def test_no_title_renders_ungrouped(self):
        assert SitemapSection(ThingSitemap).get_title() is None
