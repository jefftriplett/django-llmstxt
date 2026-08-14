from __future__ import annotations

from django.http import HttpResponse
from django.urls import path
from django.views import View

from django_llmstxt import LlmsEntry, LlmsSection
from django_llmstxt.views import LlmsFullTxtView, LlmsTxtView


class RootSection(LlmsSection):
    def items(self):
        return [
            {"title": "Pricing", "url": "/pricing/", "description": "Plans."},
            {"title": "Status", "url": "https://status.example.com"},
        ]


class DocsSection(LlmsSection):
    title = "Docs"

    def items(self):
        return [
            LlmsEntry(
                title="Getting started",
                url="/docs/start/",
                description="Install and run.",
                content="# Getting started\n\nInstall the thing.",
            ),
            LlmsEntry(
                title="Gated report",
                url="/reports/",
                description="Requires sign-in.",
                content=None,
            ),
        ]


def about(request):
    return HttpResponse(
        "<html><head><title>About</title></head>"
        "<body><h1>About</h1><p>Hello <strong>world</strong>.</p>"
        "<script>var x = 1;</script></body></html>"
    )


def handbook(request):
    return HttpResponse("<html><body><h1>Handbook</h1></body></html>")


handbook.llms_md = "# Handbook\n\nHand-written markdown.\n"


def trailing(request):
    return HttpResponse("<html><body><h1>Trailing</h1></body></html>")


def raw_markdown(request):
    return HttpResponse("# Raw\n\nServed by the project itself.\n")


class GuideView(View):
    llms_md = "# Guide\n\nCBV hand-written markdown.\n"

    def get(self, request):
        return HttpResponse("<html><body><h1>Guide</h1></body></html>")


def profile(request):
    return HttpResponse("<html><body><h1>Profile</h1></body></html>")


def profile_md(request):
    return f"# Profile\n\nRendered for {request.path_info}.\n"


profile.llms_md = profile_md


def report(request):
    response = HttpResponse("<html><body><h1>Report</h1></body></html>")
    response.llms_md = "# Report\n\nResponse-level markdown.\n"
    return response


report.llms_md = "# Report\n\nView-level markdown.\n"


urlpatterns = [
    path("about", about, name="about"),
    path("handbook", handbook, name="handbook"),
    path("raw.md", raw_markdown, name="raw-markdown"),
    path("trailing/", trailing, name="trailing"),
    path("guide", GuideView.as_view(), name="guide"),
    path("profile", profile, name="profile"),
    path("report", report, name="report"),
    path(
        "llms.txt",
        LlmsTxtView.as_view(
            sections={"root": RootSection, "docs": DocsSection},
        ),
        name="llms-txt",
    ),
    path(
        "llms-full.txt",
        LlmsFullTxtView.as_view(
            sections={"root": RootSection, "docs": DocsSection},
        ),
        name="llms-full-txt",
    ),
    path(
        "branded/llms.txt",
        LlmsTxtView.as_view(
            sections={"root": RootSection},
            site_title="Acme Docs",
            site_description="Everything about the Acme API.",
        ),
        name="llms-txt-branded",
    ),
]
