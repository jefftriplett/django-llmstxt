from __future__ import annotations

from types import SimpleNamespace

from django.http import HttpResponse
from django.test import RequestFactory

from django_llmstxt.middleware import LlmsMarkdownMiddleware, MarkdownDetails

rf = RequestFactory()


def make_middleware():
    return LlmsMarkdownMiddleware(
        lambda request: HttpResponse(
            "<html><body><h1>Hi</h1><p>Some <em>page</em>.</p></body></html>"
        )
    )


class TestMarkdownTwins:
    def test_md_suffix_converts(self, client):
        response = client.get("/about.md")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/markdown; charset=utf-8"
        body = response.text
        assert "# About" in body
        assert "**world**" in body
        assert "var x = 1" not in body  # scripts stripped

    def test_md_suffix_with_trailing_slash_route(self, client):
        response = client.get("/trailing.md")
        assert response.status_code == 200
        assert "# Trailing" in response.text

    def test_canonical_route_untouched(self, client):
        response = client.get("/about")
        assert response.headers["Content-Type"].startswith("text/html")
        assert "<h1>About</h1>" in response.text

    def test_unknown_md_route_passes_through(self, client):
        response = client.get("/nonexistent.md")
        assert response.status_code == 404

    def test_exclude_blocks_conversion(self, client, settings):
        settings.LLMSTXT = {"EXCLUDE": ["/about*"]}
        response = client.get("/about.md")
        assert response.headers["Content-Type"].startswith("text/html")

    def test_project_owned_md_route_wins(self, client):
        # The route resolves as-is, so the middleware must not touch it.
        response = client.get("/raw.md")
        assert response.status_code == 200
        assert response.text == "# Raw\n\nServed by the project itself.\n"

    def test_flatpage_twin_via_fallback_middleware(self, client, db):
        from django.contrib.flatpages.models import FlatPage
        from django.contrib.sites.models import Site

        page = FlatPage.objects.create(
            url="/about-us/",
            title="About us",
            content="<h1>About us</h1><p>We make <strong>things</strong>.</p>",
        )
        page.sites.add(Site.objects.get_current())
        response = client.get("/about-us.md")
        assert response.headers["Content-Type"] == "text/markdown; charset=utf-8"
        assert "# About us" in response.text
        assert "**things**" in response.text

    def test_view_override_wins(self, client):
        response = client.get("/handbook.md")
        assert response.text == "# Handbook\n\nHand-written markdown.\n"


class TestLlmsMdOverride:
    def test_cbv_class_attribute(self, client):
        response = client.get("/guide.md")
        assert response.headers["Content-Type"] == "text/markdown; charset=utf-8"
        assert response.text == "# Guide\n\nCBV hand-written markdown.\n"

    def test_callable_override_gets_request(self, client):
        response = client.get("/profile.md")
        assert response.text == "# Profile\n\nRendered for /profile.\n"

    def test_response_attribute_wins_over_view_attribute(self, client):
        response = client.get("/report.md")
        assert response.text == "# Report\n\nResponse-level markdown.\n"

    def test_exclude_blocks_accept_negotiation(self, client, settings):
        settings.LLMSTXT = {"EXCLUDE": ["/about*"]}
        response = client.get("/about", headers={"Accept": "text/markdown"})
        assert response.headers["Content-Type"].startswith("text/html")


class TestAcceptNegotiation:
    def test_accept_markdown_converts(self, client):
        response = client.get("/about", headers={"Accept": "text/markdown"})
        assert response.headers["Content-Type"] == "text/markdown; charset=utf-8"
        assert "# About" in response.text

    def test_vary_accept_set(self, client):
        response = client.get("/about", headers={"Accept": "text/markdown"})
        assert "Accept" in response.headers.get("Vary", "")

    def test_browser_accept_untouched(self, client):
        response = client.get(
            "/about", headers={"Accept": "text/html,application/xhtml+xml"}
        )
        assert response.headers["Content-Type"].startswith("text/html")


class TestRequestMarkdown:
    def _capture(self, path, **headers):
        seen = {}

        def get_response(request):
            seen["details"] = request.markdown
            return HttpResponse("<html><body><h1>Hi</h1></body></html>")

        middleware = LlmsMarkdownMiddleware(get_response)
        middleware(rf.get(path, **headers))
        return seen["details"]

    def test_attached_and_falsy_by_default(self):
        details = self._capture("/about")
        assert isinstance(details, MarkdownDetails)
        assert not details
        assert details.via_accept is False
        assert details.via_suffix is False

    def test_truthy_via_accept(self):
        details = self._capture("/about", HTTP_ACCEPT="text/markdown")
        assert details
        assert details.via_accept is True
        assert details.via_suffix is False

    def test_truthy_via_suffix(self):
        details = self._capture("/about.md")
        assert details
        assert details.via_suffix is True
        assert details.via_accept is False

    def test_repr(self):
        details = MarkdownDetails()
        details.via_accept = True
        assert repr(details) == ("<MarkdownDetails via_accept=True via_suffix=False>")


class TestCacheSafety:
    def test_authenticated_user_gets_private_no_store(self):
        request = rf.get("/hi.md")
        request.markdown = MarkdownDetails()
        request.markdown.via_suffix = True
        request.user = SimpleNamespace(is_authenticated=True)
        request.path_info = "/hi"

        response = make_middleware().process_response(
            request, HttpResponse("<html><body><p>Secret</p></body></html>")
        )
        assert "private" in response.headers["Cache-Control"]
        assert "no-store" in response.headers["Cache-Control"]

    def test_anonymous_user_gets_no_cache_headers(self):
        request = rf.get("/hi.md")
        request.markdown = MarkdownDetails()
        request.markdown.via_suffix = True
        request.user = SimpleNamespace(is_authenticated=False)
        request.path_info = "/hi"

        response = make_middleware().process_response(
            request, HttpResponse("<html><body><p>Public</p></body></html>")
        )
        assert "Cache-Control" not in response.headers

    def test_non_html_response_untouched(self):
        request = rf.get("/feed.xml")
        request.markdown = MarkdownDetails()
        request.markdown.via_suffix = True
        request.path_info = "/feed.xml"

        response = make_middleware().process_response(
            request, HttpResponse("<rss/>", content_type="application/rss+xml")
        )
        assert response.headers["Content-Type"] == "application/rss+xml"
