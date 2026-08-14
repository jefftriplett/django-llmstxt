from __future__ import annotations

from demo.llms import BlogSection, RootSection
from demo.views import account, handbook, post_detail
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from django_llmstxt.contrib.flatpages import FlatPagesSection
from django_llmstxt.views import LlmsFullTxtView, LlmsTxtView

sections = {
    "root": RootSection,
    "pages": FlatPagesSection,
    "blog": BlogSection,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("llms.txt", LlmsTxtView.as_view(sections=sections), name="llms-txt"),
    path(
        "llms-full.txt",
        LlmsFullTxtView.as_view(sections=sections),
        name="llms-full-txt",
    ),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path(
        "pricing/",
        TemplateView.as_view(template_name="pricing.html"),
        name="pricing",
    ),
    path("handbook/", handbook, name="handbook"),
    path("account/", account, name="account"),
    path("blog/<slug:slug>/", post_detail, name="post-detail"),
]
