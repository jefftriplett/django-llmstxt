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
