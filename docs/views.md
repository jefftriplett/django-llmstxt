# Views

Two class-based views render the index surfaces. Both subclass
`LlmsBaseView`, a thin `django.views.View`.

```python
from django_llmstxt.views import LlmsFullTxtView, LlmsTxtView

urlpatterns = [
    path("llms.txt", LlmsTxtView.as_view(sections=SECTIONS)),
    path("llms-full.txt", LlmsFullTxtView.as_view(sections=SECTIONS)),
]
```

Both respond to GET/HEAD with `Content-Type: text/markdown; charset=utf-8`.

## `LlmsTxtView`

Renders the spec-compliant index:

```markdown
# Acme

> Payments infrastructure for platforms.

- [Pricing](https://example.com/pricing/): Plans and per-transaction fees.

## Docs

- [Getting started](https://example.com/docs/start/): Install and run.
```

- `#` header from `site_title` (view attribute, then `LLMSTXT["SITE_TITLE"]`)
- `>` blockquote from `site_description` (same fallback chain)
- Untitled sections first is *your* job — declare them first in `sections`
- Entry descriptions render after a colon; entries without one render as a
  bare link

## `LlmsFullTxtView`

Same header, then per entry:

```markdown
## Docs

### Getting started

[Source](https://example.com/docs/start/)

Install the package and run the migration...
```

Entries with `content = None` get the heading and `[Source]` link but no
body — the metadata-only listing for gated pages.

## View attributes

| Attribute | Default | Meaning |
|---|---|---|
| `sections` | `{}` | `dict[str, LlmsSection \| type[LlmsSection]]`. Classes are instantiated per request; instances are used as-is. Keys are registry labels only — headings come from `Section.title`. |
| `site_title` | `None` | Overrides `LLMSTXT["SITE_TITLE"]` for this view. |
| `site_description` | `None` | Overrides `LLMSTXT["SITE_DESCRIPTION"]` for this view. |

## Absolute URLs

Entry URLs starting with `/` are expanded with
`request.build_absolute_uri()`, so indexes always carry fully-qualified
links regardless of where they're served. Entries that are already absolute
(`https://status.example.com`) pass through untouched.

## Subclassing

Standard CBV extension points, if the defaults don't fit:

```python
class RegionLlmsTxtView(LlmsTxtView):
    def get_site_title(self):
        return f"Acme {self.request.region.name}"

    def get_sections(self):
        return [RegionSection(self.request.region)]
```

## Existing surfaces win

Prefer a hand-written file? Put `llms.txt` in your static files and don't
wire the view. Prefer your own view? Write it — the package has no
middleware, finders, or checks competing for the route. The
[middleware](middleware.md) surfaces (`.md`, Accept negotiation) operate on
*your* HTML pages, not on the index routes.
