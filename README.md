# django-llmstxt

[llms.txt](https://llmstxt.org) for Django: a spec-compliant index of your
pages, a full-text companion file, and markdown representations of ordinary
HTML pages — declared the way you already declare sitemaps and syndication
feeds.

Inspired by [next-with-text](https://github.com/CyrusNuevoDia/next-with-text)
(Next.js) and shaped after [django-htmx](https://github.com/adamchainz/django-htmx)'s
packaging and `django.contrib.sitemaps` / `django.contrib.syndication`'s APIs.

**Docs:** [documentation](https://django-llmstxt.readthedocs.io/en/latest/) ·
[cookbook](https://django-llmstxt.readthedocs.io/en/latest/cookbook/) ·
[example project](https://github.com/jefftriplett/django-llmstxt/tree/main/example)

```bash
pip install django-llmstxt
```

## What you get

- **`/llms.txt`** — a spec-compliant markdown index of your pages, with real
  titles and descriptions
- **`/llms-full.txt`** — every listed page's content in one file, for bulk
  ingestion
- **`/<route>.md`** — a markdown twin of any HTML page (`/about` → `/about.md`)
- **`Accept: text/markdown`** — agents that ask a canonical URL for markdown
  get markdown; browsers are unaffected

## The index views

Declare sections like sitemaps/feeds, wire them in your URLconf:

```python
# myapp/llms.py
from django_llmstxt import LlmsSection


class DocsSection(LlmsSection):
    title = "Docs"  # renders as `## Docs`; None = ungrouped root pages

    def items(self):
        return Page.objects.published()

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary

    def item_content(self, item):  # body in llms-full.txt; None = index-only
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

Items can be model instances (above), plain dicts, `LlmsEntry` objects, or
bare URL strings — handy for static pages. Using `django.contrib.flatpages`?
Skip the boilerplate entirely:

```python
from django_llmstxt.contrib.flatpages import FlatPagesSection

sections = {"pages": FlatPagesSection}  # every flat page, content converted
```

Or static dicts:

```python
class RootSection(LlmsSection):
    def items(self):
        return [
            {"title": "Pricing", "url": "/pricing/", "description": "Plans."},
        ]
```

Produces:

```markdown
# Acme

> Payments infrastructure for platforms.

- [Pricing](https://example.com/pricing/): Plans.

## Docs

- [Getting started](https://example.com/docs/start/): Install and run.
```

## The middleware

```python
# settings.py
MIDDLEWARE = [
    # ...
    "django_llmstxt.middleware.LlmsMarkdownMiddleware",
]
```

That's it. `/about.md` now serves a markdown conversion of `/about`, and
`Accept: text/markdown` negotiates the same on the canonical URL (with
`Vary: Accept` set). Scripts, styles, and `noscript` are stripped before
conversion.

**Per-page override.** Pages whose HTML converts poorly can ship hand-written
markdown. On a function view:

```python
def handbook(request): ...


handbook.llms_md = "# Handbook\n\nHand-written markdown."
```

On a CBV, set `llms_md` as a class attribute; on either, a callable value is
called with the request. A response instance attribute `response.llms_md`
wins over the view attribute.

**Auth safety.** A markdown response rendered for an authenticated user is
sent with `Cache-Control: private, no-store`, so a shared cache can't hand
one visitor's page to the next. Pages that must never appear in the public
indexes simply aren't listed in a section — enumeration is the allowlist.
For gated pages you *want* agents to know about, list the entry with
`content = None` (or omit `item_content`): it appears in `llms.txt` and in
`llms-full.txt` as metadata plus a `[Source]` link, with no body.

## Settings

```python
LLMSTXT = {
    "SITE_TITLE": "Acme",  # `# Acme` header; views may override
    "SITE_DESCRIPTION": "Payments infra.",  # `> ...` blockquote under the header
    "INCLUDE": ["*"],  # route-path globs
    "EXCLUDE": ["/admin/*"],  # wins over INCLUDE and every surface
    "CONVERTER": "django_llmstxt.convert.html_to_markdown",  # or your callable
}
```

`EXCLUDE` is a reliable kill switch: matching routes get no `.md` conversion
and no index entries, no matter what a view or section declares.

## Development

```bash
uv sync --group test
uv run pytest
uvx ruff check --fix . && uvx ruff format .
```

## License

MIT
