# django-llmstxt documentation

[llms.txt](https://llmstxt.org) for Django: a spec-compliant index of your
pages, a full-text companion file, and markdown representations of ordinary
HTML pages.

## Guides

- [Installation](installation.md) — requirements, install, the two-minute setup
- [Sections](sections.md) — declaring what appears in your indexes (the
  sitemap/feed-style API)
- [Views](views.md) — `LlmsTxtView` and `LlmsFullTxtView`
- [Middleware](middleware.md) — `/<route>.md` twins and `Accept: text/markdown`
  negotiation
- [Settings](settings.md) — the full `LLMSTXT` dict reference
- [Cookbook](cookbook.md) — recipes: flat pages, blog models, gated pages,
  custom converters, and more

## The short version

```python
# myapp/llms.py
from django_llmstxt import LlmsSection


class DocsSection(LlmsSection):
    title = "Docs"

    def items(self):
        return Page.objects.published()

    def item_description(self, item):
        return item.summary

    def item_content(self, item):
        return item.body_markdown
```

```python
# urls.py
from django.urls import path
from django_llmstxt.views import LlmsFullTxtView, LlmsTxtView

urlpatterns = [
    path("llms.txt", LlmsTxtView.as_view(sections={"docs": DocsSection})),
    path("llms-full.txt", LlmsFullTxtView.as_view(sections={"docs": DocsSection})),
]
```

```python
# settings.py
MIDDLEWARE = [
    # ...
    "django_llmstxt.middleware.LlmsMarkdownMiddleware",
]
```

You now serve `/llms.txt`, `/llms-full.txt`, a markdown twin at
`/<route>.md` for every HTML page, and markdown to any client that sends
`Accept: text/markdown`.

## Design principles

1. **Enumeration is the auth boundary.** Indexes are built from what you
   explicitly list in sections — never from crawling rendered output. A page
   that isn't listed doesn't exist as far as agents are concerned, and there
   is no build artifact to leak.
2. **Zero config where possible, one-line overrides where not.** Default
   HTML→markdown conversion, default index templates, default globs. Override
   per page (`llms_md`), per view (attributes), or per project (`LLMSTXT`).
3. **Existing surfaces win.** Wire your own view for `/llms.txt` instead and
   nothing in the package fights you for the route.
4. **Familiar APIs.** If you've written a `django.contrib.sitemaps.Sitemap`
   or a `django.contrib.syndication.Feed` subclass, you already know how to
   write a `LlmsSection`.

## Layout

| Module | Purpose |
|---|---|
| `django_llmstxt.sections` | `LlmsSection`, `LlmsEntry`, glob filtering |
| `django_llmstxt.views` | `LlmsTxtView`, `LlmsFullTxtView` |
| `django_llmstxt.middleware` | `LlmsMarkdownMiddleware` |
| `django_llmstxt.conf` | `LLMSTXT` settings access |
| `django_llmstxt.convert` | Default HTML→markdown converter |
| `django_llmstxt.contrib.flatpages` | `FlatPagesSection` for django.contrib.flatpages |
