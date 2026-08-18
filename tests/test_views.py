from __future__ import annotations


class TestLlmsTxtView:
    def test_index_structure(self, client):
        response = client.get("/llms.txt")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/markdown; charset=utf-8"
        body = response.text
        assert body.startswith("# Test Site\n")
        assert "> A site used by the test suite." in body
        # Untitled section renders before the first heading.
        assert body.index("- [Pricing]") < body.index("## Docs")
        assert "- [Pricing](http://testserver/pricing/): Plans." in body
        assert (
            "- [Getting started](http://testserver/docs/start/): Install and run."
            in body
        )

    def test_optional_section_renders_optional_heading(self, client):
        body = client.get("/llms.txt").text
        assert "## Optional" in body
        assert "- [Changelog](http://testserver/changelog/)" in body
        # Declaration order: Optional comes after the Docs section.
        assert body.index("## Docs") < body.index("## Optional")

    def test_exclude_killswitch(self, client, settings):
        settings.LLMSTXT = {
            "SITE_TITLE": "Test Site",
            "EXCLUDE": ["/pricing/"],
        }
        response = client.get("/llms.txt")
        assert "[Pricing]" not in response.text
        assert "[Getting started]" in response.text

    def test_absolute_urls_pass_through_untouched(self, client):
        response = client.get("/llms.txt")
        assert "- [Status](https://status.example.com)" in response.text

    def test_per_view_site_title_and_description(self, client):
        response = client.get("/branded/llms.txt")
        body = response.text
        assert body.startswith("# Acme Docs\n")
        assert "> Everything about the Acme API." in body
        assert "Test Site" not in body

    def test_per_view_site_details_render_after_blockquote(self, client):
        body = client.get("/branded/llms.txt").text
        detail = "Start with the quickstart, then the reference."
        assert detail in body
        # Content section sits between the blockquote and the first H2 list.
        assert body.index("> Everything") < body.index(detail)
        assert body.index(detail) < body.index("- [Pricing]")

    def test_site_details_setting(self, client, settings):
        settings.LLMSTXT = {
            "SITE_TITLE": "Test Site",
            "SITE_DESCRIPTION": "A site used by the test suite.",
            "SITE_DETAILS": "This file indexes the docs.",
        }
        body = client.get("/llms.txt").text
        assert body.index("> A site used") < body.index("This file indexes the docs.")
        assert body.index("This file indexes the docs.") < body.index("## Docs")

    def test_no_site_details_by_default(self, client):
        # Header goes straight from blockquote to the first section.
        body = client.get("/llms.txt").text
        assert "> A site used by the test suite.\n\n- [Pricing]" in body


class TestConditionalGet:
    def test_index_sends_an_etag(self, client):
        assert client.get("/llms.txt").headers["ETag"]

    def test_full_sends_an_etag(self, client):
        assert client.get("/llms-full.txt").headers["ETag"]

    def test_matching_if_none_match_returns_304(self, client):
        etag = client.get("/llms.txt").headers["ETag"]
        response = client.get("/llms.txt", headers={"If-None-Match": etag})
        assert response.status_code == 304
        assert response.headers["ETag"] == etag

    def test_stale_if_none_match_returns_full_body(self, client):
        response = client.get("/llms.txt", headers={"If-None-Match": '"stale"'})
        assert response.status_code == 200
        assert response.text.startswith("# Test Site")

    def test_etag_changes_when_content_changes(self, client, settings):
        first = client.get("/llms.txt").headers["ETag"]
        settings.LLMSTXT = {"SITE_TITLE": "Renamed", "SITE_DESCRIPTION": ""}
        second = client.get("/llms.txt").headers["ETag"]
        assert first != second


class TestLlmsFullTxtView:
    def test_full_text(self, client):
        response = client.get("/llms-full.txt")
        assert response.status_code == 200
        body = response.text
        assert body.startswith("# Test Site\n")
        assert "## Docs" in body
        assert "### Getting started" in body
        assert "[Source](http://testserver/docs/start/)" in body
        assert "# Getting started\n\nInstall the thing." in body

    def test_contentless_entry_is_metadata_only(self, client):
        response = client.get("/llms-full.txt")
        body = response.text
        assert "### Gated report" in body
        assert "[Source](http://testserver/reports/)" in body
