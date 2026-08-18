from __future__ import annotations

from django.template import Context, Template
from django.test import RequestFactory, override_settings

from django_llmstxt.utils import (
    build_link_header,
    llms_txt_url,
    markdown_candidates,
    markdown_url,
)

rf = RequestFactory()


class TestMarkdownUrlForms:
    """v2 allows an appended .md, a replaced extension, and index.md."""

    def test_appended_suffix_on_a_file_name(self, client):
        response = client.get("/page.html.md")
        assert response.status_code == 200
        assert "# Page" in response.text

    def test_replaced_extension(self, client):
        response = client.get("/page.md")
        assert response.status_code == 200
        assert "# Page" in response.text

    def test_index_md_names_the_directory(self, client):
        response = client.get("/trailing/index.md")
        assert response.status_code == 200
        assert "# Trailing" in response.text

    def test_candidates_are_most_specific_first(self):
        assert markdown_candidates("/docs/index.md") == [
            "/docs/index",
            "/docs/index/",
            "/docs/",
            "/docs/index.html",
        ]

    def test_candidates_of_a_file_name_skip_extension_replacement(self):
        assert markdown_candidates("/page.html.md") == ["/page.html", "/page.html/"]

    def test_markdown_url_of_a_directory_uses_index(self):
        assert markdown_url("/docs/") == "/docs/index.md"

    def test_markdown_url_of_a_file_appends(self):
        assert markdown_url("/page.html") == "/page.html.md"


class TestLinkHeader:
    def test_html_response_advertises_both_relations(self, client):
        link = client.get("/about").headers["Link"]
        assert '</about.md>; rel="alternate"; type="text/markdown"' in link
        assert '</llms.txt>; rel="describedby"' in link

    def test_markdown_response_omits_the_alternate(self, client):
        link = client.get("/about.md").headers["Link"]
        assert "alternate" not in link
        assert '</llms.txt>; rel="describedby"' in link

    def test_most_specific_llms_txt_wins(self, client):
        link = client.get("/branded/tour").headers["Link"]
        assert '</branded/llms.txt>; rel="describedby"' in link

    @override_settings(LLMSTXT={"LINK_HEADERS": False})
    def test_setting_disables_the_header(self, client):
        assert "Link" not in client.get("/about").headers

    def test_excluded_path_gets_no_header(self, client):
        with override_settings(LLMSTXT={"EXCLUDE": ["/about"]}):
            assert "Link" not in client.get("/about").headers

    def test_build_link_header_renders_one_relation(self):
        assert build_link_header(describedby="/llms.txt") == (
            '</llms.txt>; rel="describedby"'
        )

    def test_build_link_header_is_empty_without_links(self):
        assert build_link_header() == ""


class TestCoverage:
    def test_root_file_covers_an_unbranded_path(self):
        assert llms_txt_url("/about") == "/llms.txt"

    def test_specific_file_covers_its_own_subtree(self):
        assert llms_txt_url("/branded/tour") == "/branded/llms.txt"

    def test_directory_path_is_covered(self):
        assert llms_txt_url("/branded/") == "/branded/llms.txt"


class TestTemplateTag:
    def render(self, path):
        template = Template("{% load llmstxt %}{% llms_links %}")
        return template.render(Context({"request": rf.get(path)}))

    def test_renders_both_link_elements(self):
        html = self.render("/branded/tour")
        assert '<link rel="alternate" type="text/markdown" ' in html
        assert 'href="/branded/tour.md">' in html
        assert '<link rel="describedby" href="/branded/llms.txt">' in html

    def test_without_a_request_renders_nothing(self):
        template = Template("{% load llmstxt %}{% llms_links %}")
        assert template.render(Context({})) == ""


class TestVaryHeader:
    def test_html_response_varies_on_accept(self, client):
        assert "Accept" in client.get("/about").headers["Vary"]

    def test_markdown_twin_does_not_vary(self, client):
        # A .md twin is a distinct URL, not a negotiated representation.
        assert "Vary" not in client.get("/about.md").headers

    def test_negotiated_markdown_still_varies(self, client):
        response = client.get("/about", headers={"Accept": "text/markdown"})
        assert "Accept" in response.headers["Vary"]

    def test_excluded_path_does_not_vary(self, client):
        with override_settings(LLMSTXT={"EXCLUDE": ["/about"]}):
            assert "Vary" not in client.get("/about").headers
