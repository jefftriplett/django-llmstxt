from __future__ import annotations

import pytest
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site

from django_llmstxt.contrib.flatpages import (
    FlatPagesIndexSection,
    FlatPagesSection,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def flatpage():
    page = FlatPage.objects.create(
        url="/about/",
        title="About us",
        content="<h1>About us</h1><p>We make <strong>things</strong>.</p>",
    )
    page.sites.add(Site.objects.get_current())
    return page


@pytest.fixture
def second_flatpage():
    page = FlatPage.objects.create(
        url="/legal/",
        title="Legal",
        content="<p>Terms apply.</p>",
    )
    page.sites.add(Site.objects.get_current())
    return page


class TestFlatPagesSection:
    def test_entries_from_flatpages(self, flatpage):
        (entry,) = FlatPagesSection().get_entries()
        assert entry.title == "About us"
        assert entry.url == "/about/"

    def test_content_is_converted_to_markdown(self, flatpage):
        (entry,) = FlatPagesSection().get_entries()
        assert entry.content is not None
        assert "**things**" in entry.content
        assert "<strong>" not in entry.content

    def test_section_heading_default(self):
        assert FlatPagesSection.title == "Pages"

    def test_ordering_by_url(self, flatpage, second_flatpage):
        entries = FlatPagesSection().get_entries()
        assert [e.url for e in entries] == ["/about/", "/legal/"]

    def test_other_sites_pages_are_not_listed(self, flatpage):
        other_site = Site.objects.create(domain="other.example.com", name="other")
        page = FlatPage.objects.create(
            url="/elsewhere/",
            title="Elsewhere",
            content="<p>Not this site.</p>",
        )
        page.sites.add(other_site)
        entries = FlatPagesSection().get_entries()
        assert [e.url for e in entries] == ["/about/"]


class TestFlatPagesIndexSection:
    def test_content_is_none(self, flatpage):
        (entry,) = FlatPagesIndexSection().get_entries()
        assert entry.content is None
        assert entry.title == "About us"
