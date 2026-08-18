# Settings

All configuration lives in a single `LLMSTXT` dict in your Django settings.
Every key is optional; the defaults shown below.

```python
LLMSTXT = {
    "SITE_TITLE": "",
    "SITE_DESCRIPTION": "",
    "SITE_DETAILS": "",
    "INCLUDE": ["*"],
    "EXCLUDE": [],
    "LINK_HEADERS": True,
    "CONVERTER": "django_llmstxt.convert.html_to_markdown",
}
```

## `SITE_TITLE`

Default `#` header for both index views. A view's `site_title` attribute
wins over this. With neither set, the header is `llms.txt`.

```python
LLMSTXT = {"SITE_TITLE": "Acme"}
```

## `SITE_DESCRIPTION`

Default `>` blockquote under the header. A view's `site_description`
attribute wins. Empty = no blockquote.

## `SITE_DETAILS`

Free markdown for the spec's **content section** — placed between the
blockquote and the first `## H2` list in both index views. A view's
`site_details` attribute wins. Empty = no content section. See
[Content sections](views.md#content-sections-site_details).

```python
LLMSTXT = {"SITE_DETAILS": "Start with the quickstart, then the reference."}
```

## `INCLUDE` / `EXCLUDE`

Route-path globs (matched with `fnmatch.fnmatchcase` against the path, so
`*` crosses `/`). Both surfaces respect them:

- **Middleware** — an excluded route gets no `.md` conversion and no Accept
  negotiation; the original HTML is served
- **Indexes** — `LlmsSection.get_entries()` drops excluded URLs, whatever
  the section declared

`EXCLUDE` always wins over `INCLUDE`. It is the reliable kill switch:

```python
LLMSTXT = {
    "INCLUDE": ["*"],
    "EXCLUDE": ["/admin/*", "/accounts/*", "/internal/dashboard"],
}
```

## `LINK_HEADERS`

Whether the middleware adds the llms.txt v2 discovery relations to a
response as a `Link:` header — `rel="alternate"` for the markdown twin, and
`rel="describedby"` for the covering `llms.txt` file. See
[Discovery](middleware.md#discovery-link-relations).

Set it to `False` when your CDN or web server already adds the header:

```python
LLMSTXT = {"LINK_HEADERS": False}
```

The `{% llms_links %}` template tag is unaffected by this setting.

## `CONVERTER`

Callable turning an HTML document into markdown, used by the middleware
(for pages without an `llms_md` override) and by
`FlatPagesSection.item_content()`:

```python
def converter(html: str, *, url: str = "") -> str: ...
```

- `html` — the full response body, decoded
- `url` — the absolute URL being served (handy for resolving relative
  links)

Set it as a callable or a dotted import path:

```python
LLMSTXT = {"CONVERTER": "myapp.markdown.clean_converter"}
```

See the [custom converter recipe](cookbook.md#8-strip-site-chrome-with-a-custom-converter)
for a worked example that removes nav/footer chrome before conversion.

## Runtime behavior

Settings are read lazily on every access, so `override_settings({"LLMSTXT":
...})` works in tests:

```python
from django.test import override_settings


@override_settings(LLMSTXT={"EXCLUDE": ["/pricing/"]})
def test_pricing_is_hidden(self): ...
```
