from __future__ import annotations

import pytest

from django_llmstxt import LlmsEntry, LlmsSection
from django_llmstxt.utils import accepts_markdown


class DictSection(LlmsSection):
    def items(self):
        return [
            {"title": "Pricing", "url": "/pricing/", "description": "Plans."},
            {"title": "About", "url": "/about/"},
        ]


class ModelLike:
    def __init__(self, title, url):
        self.title = title
        self.url = url

    def get_absolute_url(self):
        return self.url

    def __str__(self):
        return self.title


class ModelSection(LlmsSection):
    title = "Blog"

    def items(self):
        return [ModelLike("Hello", "/blog/hello/")]


class TestGetTitle:
    def test_plain_section_uses_title(self):
        assert ModelSection().get_title() == "Blog"

    def test_untitled_section_is_none(self):
        assert DictSection().get_title() is None

    def test_optional_defaults_to_optional_heading(self):
        class Extras(LlmsSection):
            optional = True

        assert Extras().get_title() == "Optional"

    def test_optional_respects_explicit_title(self):
        class Extras(LlmsSection):
            optional = True
            title = "Further reading"

        assert Extras().get_title() == "Further reading"


class TestGetEntries:
    def test_dict_items(self):
        entries = DictSection().get_entries()
        assert entries[0] == LlmsEntry(
            title="Pricing", url="/pricing/", description="Plans."
        )
        assert entries[1].description == ""
        assert entries[1].content is None

    def test_object_items_use_get_absolute_url(self):
        entries = ModelSection().get_entries()
        assert entries[0].title == "Hello"
        assert entries[0].url == "/blog/hello/"

    def test_string_item_is_a_url(self):
        class UrlSection(LlmsSection):
            def items(self):
                return ["/plain/"]

        entries = UrlSection().get_entries()
        assert entries[0].url == "/plain/"
        assert entries[0].title == "/plain/"

    def test_missing_url_raises(self):
        class BadSection(LlmsSection):
            def items(self):
                return [object()]

        with pytest.raises(TypeError, match="Cannot determine URL"):
            BadSection().get_entries()

    def test_exclude_glob_drops_entries(self, settings):
        settings.LLMSTXT = {"EXCLUDE": ["/pricing/"]}
        entries = DictSection().get_entries()
        assert [e.url for e in entries] == ["/about/"]

    def test_include_glob_restricts_entries(self, settings):
        settings.LLMSTXT = {"INCLUDE": ["/docs/*"]}
        entries = DictSection().get_entries()
        assert entries == []

    def test_exclude_wins_over_include(self, settings):
        settings.LLMSTXT = {"INCLUDE": ["/pricing/*"], "EXCLUDE": ["/pricing/"]}
        entries = DictSection().get_entries()
        assert entries == []


class TestAcceptsMarkdown:
    @pytest.mark.parametrize(
        "header",
        [
            "text/markdown",
            "text/html, text/markdown",
            "text/html;q=0.9, text/markdown;q=0.8",
            "TEXT/MARKDOWN",
        ],
    )
    def test_accepts(self, header):
        assert accepts_markdown(header)

    @pytest.mark.parametrize(
        "header",
        [
            "",
            "text/html",
            "text/markdown;q=0",
            "text/html, application/json",
        ],
    )
    def test_rejects(self, header):
        assert not accepts_markdown(header)
