# Sections

Sections are how you declare what appears in `/llms.txt` and
`/llms-full.txt`. The API follows `django.contrib.sitemaps` and
`django.contrib.syndication`: subclass `LlmsSection`, override `items()` and
the `item_*` hooks, hand the class to a view.

```python
from django_llmstxt import LlmsSection


class DocsSection(LlmsSection):
    title = "Docs"

    def items(self):
        return Page.objects.published()

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary

    def item_content(self, item):
        return item.body_markdown
```

## Class attributes

| Attribute | Default | Meaning |
|---|---|---|
| `title` | `None` | Section heading, rendered as `## {title}`. `None` = ungrouped entries rendered before any heading (use for root-level pages). |
| `description` | `None` | Reserved for future use; not currently rendered. |

## Methods

| Method | Default | Override to |
|---|---|---|
| `items()` | `[]` | Return an iterable (queryset, list, generator) of pages. |
| `item_title(item)` | `str(item)` | Page title for the index. |
| `item_url(item)` | `item["url"]` / `item.url` / `item.get_absolute_url()` / the string itself | Page path or absolute URL. |
| `item_description(item)` | `""` | One-line description shown after the link. |
| `item_content(item)` | `None` | Full markdown body for `llms-full.txt`. `None` = metadata-only. |
| `get_entries()` | — | Returns the final `list[LlmsEntry]`, after glob filtering. Rarely overridden. |

## What items can be

Four shapes, mixable in one `items()`:

```python
def items(self):
    return [
        # 1. Plain dict — great for static pages
        {"title": "Pricing", "url": "/pricing/", "description": "Plans."},
        # 2. LlmsEntry — the explicit dataclass
        LlmsEntry(title="Status", url="https://status.example.com"),
        # 3. A bare string — treated as a URL (title falls back to the URL)
        "/about/",
        # 4. Anything else — item_title/item_url/... are called on it,
        #    with get_absolute_url() used by default
        *Page.objects.published(),
    ]
```

`item_content()` returning `None` means the page is listed in `llms.txt` and
in `llms-full.txt` (as title + `[Source]` link) but has **no published
body** — the metadata-only opt-in for gated pages.

## Ordering

Sections render in the order the `sections={...}` dict declares them, and
entries in the order `items()` yields them. Put an untitled section first to
open the file with root-level pages, matching the llms.txt convention:

```python
sections = {"root": RootSection, "docs": DocsSection, "blog": BlogSection}
```

## Glob filtering

`get_entries()` drops any entry whose URL fails the
[`INCLUDE`/`EXCLUDE`](settings.md) globs. `EXCLUDE` always wins — it's the
kill switch that overrides whatever a section declares:

```python
LLMSTXT = {"EXCLUDE": ["/internal/*"]}
```

Filtering applies to the entry URL as written — usually a path like
`/docs/start/`. Absolute URLs are matched as-is, so exclude patterns should
target paths (`*/internal/*` for absolute-URL entries).

## Reusing a section across indexes

One section class feeds both views — this is the intended usage:

```python
SECTIONS = {"root": RootSection, "docs": DocsSection}

urlpatterns = [
    path("llms.txt", LlmsTxtView.as_view(sections=SECTIONS)),
    path("llms-full.txt", LlmsFullTxtView.as_view(sections=SECTIONS)),
]
```

## Built-in: flat pages

`django_llmstxt.contrib.flatpages.FlatPagesSection` covers
`django.contrib.flatpages` out of the box, converting each page's HTML
content with the configured converter. See the
[cookbook](cookbook.md#1-flat-pages-zero-code).
