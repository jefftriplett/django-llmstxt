# Cookbook

Worked recipes, smallest first. Everything here runs against stock Django —
the only third-party import anywhere is django-llmstxt itself.

## Contents

1. [Flat pages, zero code](#1-flat-pages-zero-code)
2. [Flat pages, metadata-only](#2-flat-pages-metadata-only)
3. [Blog posts from a model](#3-blog-posts-from-a-model)
4. [Marketing pages as static dicts](#4-marketing-pages-as-static-dicts)
5. [Root pages first, then sections](#5-root-pages-first-then-sections)
6. [List a gated page without publishing its content](#6-list-a-gated-page-without-publishing-its-content)
7. [Hand-written markdown for one page](#7-hand-written-markdown-for-one-page)
8. [Strip site chrome with a custom converter](#8-strip-site-chrome-with-a-custom-converter)
9. [Exclude admin and account areas everywhere](#9-exclude-admin-and-account-areas-everywhere)
10. [Per-view site title (multi-brand)](#10-per-view-site-title-multi-brand)
11. [Indexes without the middleware](#11-indexes-without-the-middleware)
12. [Test your sections](#12-test-your-sections)

---

## 1. Flat pages, zero code

`django.contrib.flatpages` is built in, and so is its section.

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django.contrib.sites",
    "django.contrib.flatpages",
    "django_llmstxt",
]
SITE_ID = 1

MIDDLEWARE = [
    # ...
    "django_llmstxt.middleware.LlmsMarkdownMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",  # last
]
```

```python
# urls.py
from django.contrib.flatpages.models import FlatPage
from django.urls import path
from django_llmstxt.contrib.flatpages import FlatPagesSection
from django_llmstxt.views import LlmsFullTxtView, LlmsTxtView

SECTIONS = {"pages": FlatPagesSection}

urlpatterns = [
    path("llms.txt", LlmsTxtView.as_view(sections=SECTIONS)),
    path("llms-full.txt", LlmsFullTxtView.as_view(sections=SECTIONS)),
]
```

Every flat page now appears under `## Pages`, its HTML content converted to
markdown for `llms-full.txt`, and `/about.md` twins work through the
fallback middleware (that's why llmstxt's middleware goes **before** it).

Subclass to filter or regroup:

```python
class LegalSection(FlatPagesSection):
    title = "Legal"

    def get_queryset(self):
        return super().get_queryset().filter(url__startswith="/legal/")
```

## 2. Flat pages, metadata-only

Want agents to know the pages exist without bulk-publishing their bodies?

```python
from django_llmstxt.contrib.flatpages import FlatPagesIndexSection

# Listed in llms.txt; llms-full.txt gets title + [Source] link, no body.
SECTIONS = {"pages": FlatPagesIndexSection}
```

## 3. Blog posts from a model

The sitemap/feed pattern, verbatim. If your model stores markdown, this is
three lines of hooks:

```python
# blog/llms.py
from django_llmstxt import LlmsSection
from blog.models import Post


class BlogSection(LlmsSection):
    title = "Blog"

    def items(self):
        return Post.objects.published().order_by("-pub_date")

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary

    def item_url(self, item):
        return item.get_absolute_url()  # the default; shown for clarity

    def item_content(self, item):
        return item.body  # already markdown
```

Model stores HTML instead? Convert it:

```python
from django_llmstxt.conf import app_settings

    def item_content(self, item):
        return app_settings.CONVERTER(item.body_html, url=item.get_absolute_url())
```

## 4. Marketing pages as static dicts

No model needed. Dicts accept `title`, `url`, `description`, and an optional
`content` key:

```python
class RootSection(LlmsSection):
    def items(self):
        return [
            {"title": "Home", "url": "/"},
            {
                "title": "Pricing",
                "url": "/pricing/",
                "description": "Plans and per-transaction fees.",
                "content": "# Pricing\n\n- Starter: $0\n- Pro: $49/mo",
            },
            {"title": "Status", "url": "https://status.example.com"},
        ]
```

Absolute URLs pass through untouched — external pages belong in the index
too.

## 5. Root pages first, then sections

Render order = dict order. Declare an untitled section first to match the
llms.txt convention of opening with top-level pages:

```python
SECTIONS = {
    "root": RootSection,  # no title → bare links, no ## heading
    "docs": DocsSection,  # ## Docs
    "blog": BlogSection,  # ## Blog
}

urlpatterns = [
    path("llms.txt", LlmsTxtView.as_view(sections=SECTIONS)),
    path("llms-full.txt", LlmsFullTxtView.as_view(sections=SECTIONS)),
]
```

Result:

```markdown
# Acme

> Payments infrastructure.

- [Pricing](https://example.com/pricing/): Plans and fees.

## Docs

- [Getting started](https://example.com/docs/start/): Install and run.

## Blog

- [Why we rebuilt](https://example.com/blog/rebuild/): A postmortem.
```

## 6. List a gated page without publishing its content

The metadata-only opt-in: the entry appears in `llms.txt`, appears in
`llms-full.txt` with a `[Source]` link, and no body is published anywhere.
`/account.md` still works live — rendered with the caller's own session and
sent `Cache-Control: private, no-store`.

```python
class RootSection(LlmsSection):
    def items(self):
        return [
            {"title": "Pricing", "url": "/pricing/"},
            {
                "title": "Your account",
                "url": "/account/",
                "description": "Billing and settings. Requires sign-in.",
                # no "content" key → metadata-only
            },
        ]
```

For a gated page you *do* want to describe properly, write the body
yourself in the dict's `content` — you typed it, so it's safe to publish.

## 7. Hand-written markdown for one page

For a page whose HTML converts poorly, set `llms_md`:

```python
# Function view
def dashboard(request):
    return render(request, "dashboard.html")


dashboard.llms_md = (
    "# Dashboard\n\nApp-like page; query params documented at /docs/api/."
)
```

```python
# Class-based view
class DashboardView(TemplateView):
    template_name = "dashboard.html"
    llms_md = "# Dashboard\n\nApp-like page."
```

```python
# Dynamic — a callable gets the request
def dashboard_md(request):
    plan = getattr(request.user, "plan", "anonymous")
    return f"# Dashboard\n\nRendered for plan: {plan}."


dashboard.llms_md = dashboard_md
```

```python
# Last word — set it on the response inside the view
def report(request):
    response = render(request, "report.html")
    response.llms_md = generate_report_markdown(request)
    return response
```

Precedence: response attribute → view attribute → HTML conversion.

## 8. Strip site chrome with a custom converter

The default converter drops scripts and styles but keeps your nav and
footer. A 10-line converter removes chrome by CSS selector first:

```python
# myapp/markdown.py
import re

from bs4 import BeautifulSoup
from markdownify import markdownify


def clean_converter(html: str, *, url: str = "") -> str:
    soup = BeautifulSoup(html, "html.parser")
    for selector in ["script", "style", "nav", "footer", ".cookie-banner"]:
        for tag in soup.select(selector):
            tag.decompose()
    main = soup.select_one("main") or soup  # prefer the content column
    md = markdownify(str(main), heading_style="ATX", bullets="-")
    return re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
```

```python
LLMSTXT = {"CONVERTER": "myapp.markdown.clean_converter"}
```

The middleware and `FlatPagesSection` both pick this up.

## 9. Exclude admin and account areas everywhere

One setting covers both the middleware and the indexes — no `.md` twin, no
negotiation, no index entry, whatever a section or view declares:

```python
LLMSTXT = {
    "EXCLUDE": ["/admin/*", "/accounts/*", "/api/internal/*"],
}
```

Combined with the enumeration-is-the-boundary design, this is belt *and*
braces: excluded routes stay dark even if a section accidentally lists one.

## 10. Per-view site title (multi-brand)

View attributes beat the settings dict, so one project can serve several
branded indexes:

```python
urlpatterns = [
    path(
        "llms.txt",
        LlmsTxtView.as_view(
            sections=SECTIONS,
            site_title="Acme Docs",
            site_description="Everything about the Acme API.",
        ),
    ),
    path(
        "developers/llms.txt",
        LlmsTxtView.as_view(
            sections={"api": ApiReferenceSection},
            site_title="Acme for Developers",
        ),
    ),
]
```

## 11. Indexes without the middleware

The two halves are independent. API-only site, or pages you don't want
twin-ed? Wire only the views:

```python
urlpatterns = [
    path("llms.txt", LlmsTxtView.as_view(sections=SECTIONS)),
    path("llms-full.txt", LlmsFullTxtView.as_view(sections=SECTIONS)),
]
```

No middleware, no `.md` twins, no negotiation. The sections API is
unchanged.

## 12. Test your sections

Sections are plain Python — no request needed. Settings read lazily, so
`override_settings` exercises the globs:

```python
import pytest
from django.test import override_settings

from myapp.llms import BlogSection


@pytest.mark.django_db
def test_blog_section_lists_published_only(post, draft):
    urls = [e.url for e in BlogSection().get_entries()]
    assert post.get_absolute_url() in urls
    assert draft.get_absolute_url() not in urls


@override_settings(LLMSTXT={"EXCLUDE": ["/blog/*"]})
def test_exclude_is_a_killswitch(post):
    assert BlogSection().get_entries() == []
```

End-to-end smoke tests with Django's test client:

```python
def test_llms_txt(client):
    body = client.get("/llms.txt").text
    assert body.startswith("# Acme\n")
    assert "- [Pricing](http://testserver/pricing/)" in body


def test_markdown_twin(client):
    response = client.get("/pricing.md")
    assert response.headers["Content-Type"] == "text/markdown; charset=utf-8"


def test_accept_negotiation_sets_vary(client):
    response = client.get("/pricing/", headers={"Accept": "text/markdown"})
    assert "Accept" in response.headers["Vary"]
```

## 13. Validate your llms.txt in CI

`validate_llmstxt` checks a rendered **index** against the spec's format —
one H1 title, and every file-list bullet a real markdown link. It returns a
list of problems (empty means it's well-formed), so it drops straight into a
test that fails the build if the file drifts out of shape:

```python
from django_llmstxt import validate_llmstxt


def test_llms_txt_is_well_formed(client):
    problems = validate_llmstxt(client.get("/llms.txt").text)
    assert not problems, problems
```

It validates the `llms.txt` index, not `llms-full.txt` — the full file
embeds page bodies whose own headings and lists are not index entries.
Fenced code blocks in the [content section](views.md#content-sections-site_details)
are ignored, so a code sample there won't trip the check.
