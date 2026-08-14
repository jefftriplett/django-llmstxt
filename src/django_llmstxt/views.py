from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.views import View

from django_llmstxt.conf import app_settings
from django_llmstxt.sections import LlmsEntry, LlmsSection

MARKDOWN_CONTENT_TYPE = "text/markdown; charset=utf-8"


class LlmsBaseView(View):
    """
    Shared plumbing for the index views.

    Wire sections in your URLconf, sitemap-style:

        path("llms.txt", LlmsTxtView.as_view(sections={"docs": DocsSection}))

    The dict key is a registry label only; the rendered ``## Heading`` comes
    from ``Section.title``. Declaration order is render order — put an
    untitled section first to open the file with root-level pages.
    """

    site_title: str | None = None
    site_description: str | None = None
    sections: dict[str, type[LlmsSection] | LlmsSection] = {}

    def get_site_title(self) -> str:
        return self.site_title or app_settings.SITE_TITLE or "llms.txt"

    def get_site_description(self) -> str:
        return self.site_description or app_settings.SITE_DESCRIPTION

    def get_sections(self) -> list[LlmsSection]:
        resolved = []
        for section in self.sections.values():
            resolved.append(section() if isinstance(section, type) else section)
        return resolved

    def get_section_entries(
        self, request: HttpRequest
    ) -> list[tuple[LlmsSection, list[LlmsEntry]]]:
        return [(section, section.get_entries()) for section in self.get_sections()]

    def absolute_url(self, request: HttpRequest, url: str) -> str:
        if url.startswith("/"):
            return request.build_absolute_uri(url)
        return url

    def render_entry_link(self, request: HttpRequest, entry: LlmsEntry) -> str:
        href = self.absolute_url(request, entry.url)
        line = f"- [{entry.title}]({href})"
        if entry.description:
            line += f": {entry.description}"
        return line

    def render_header(self) -> list[str]:
        lines = [f"# {self.get_site_title()}", ""]
        description = self.get_site_description()
        if description:
            lines += [f"> {description}", ""]
        return lines

    def markdown_response(self, lines: list[str]) -> HttpResponse:
        body = "\n".join(lines).strip() + "\n"
        return HttpResponse(body, content_type=MARKDOWN_CONTENT_TYPE)


class LlmsTxtView(LlmsBaseView):
    """
    Renders a spec-compliant (llmstxt.org) markdown index:

        # Site Title

        > Site description.

        - [Pricing](https://example.com/pricing/): Plans.

        ## Docs

        - [Getting started](https://example.com/docs/start/): Install.
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        lines = self.render_header()
        for section, entries in self.get_section_entries(request):
            if section.title is not None:
                lines += [f"## {section.title}", ""]
            for entry in entries:
                lines.append(self.render_entry_link(request, entry))
            lines.append("")
        return self.markdown_response(lines)


class LlmsFullTxtView(LlmsBaseView):
    """
    Renders llms-full.txt: every section's entries with their content bodies,
    for bulk ingestion. Entries whose content is None are listed with just a
    source link — the metadata-only opt-in for gated pages.
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        lines = self.render_header()
        for section, entries in self.get_section_entries(request):
            if section.title is not None:
                lines += [f"## {section.title}", ""]
            for entry in entries:
                href = self.absolute_url(request, entry.url)
                lines += [f"### {entry.title}", "", f"[Source]({href})", ""]
                if entry.content is not None:
                    lines += [entry.content.strip(), ""]
        return self.markdown_response(lines)
