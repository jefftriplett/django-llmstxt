# Middleware

`LlmsMarkdownMiddleware` serves markdown representations of your ordinary
HTML pages — no view changes required.

```python
MIDDLEWARE = [
    # ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_llmstxt.middleware.LlmsMarkdownMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",  # last
]
```

The middleware is sync/async dual-capable (`sync_capable = async_capable =
True`, `markcoroutinefunction` — the modern Django middleware shape) and
does no work at all unless a request asks for markdown.

## `/<route>.md` twins

A GET/HEAD request ending in `.md` is rewritten to the canonical route
before URL resolution. The view renders normally; the HTML response is
converted to markdown on the way out.

The v2 spec allows more than one way to name the markdown twin, so the
middleware tries these candidates in order, and takes the first that
resolves:

| Request | Candidates |
| --- | --- |
| `/docs/intro.md` | `/docs/intro`, `/docs/intro/`, `/docs/intro.html` |
| `/page.html.md` | `/page.html`, `/page.html/` |
| `/docs/index.md` | `/docs/index`, `/docs/index/`, `/docs/` |
| `/docs/index.html.md` | `/docs/index.html`, `/docs/index.html/`, `/docs/` |

The appended form (`/page.html.md`) and the replaced extension (`/page.md`)
are both spec-blessed. A path without a file name is named by `index.md` or
`index.html.md`, either of which resolves to the directory itself.

If neither stripped path resolves in the URLconf, the request is still
rewritten optimistically so a fallback middleware (e.g.
`FlatpageFallbackMiddleware`) can serve the canonical route; if nothing
serves it, the resulting response (typically a 404) passes through
unconverted. `.md` files you serve deliberately — routes that resolve as-is
— are never intercepted.

## `Accept: text/markdown`

A request to a canonical URL whose `Accept` header allows `text/markdown`
(or `text/x-markdown`) with `q > 0` gets the same conversion. Browsers'
`Accept: text/html,...` is unaffected.

Both representations of the canonical URL are sent with `Vary: Accept`, so a
shared cache never hands the HTML to an agent that asked for markdown. A
`.md` twin is a separate URL, so it carries no `Vary` header.

## Discovery: link relations

The v2 spec asks a page to say where its markdown twin and its covering
`llms.txt` file live. The middleware adds both as a `Link:` response header,
with no configuration:

```http
GET /docs/intro HTTP/1.1

HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Link: </docs/intro.md>; rel="alternate"; type="text/markdown",
      </docs/llms.txt>; rel="describedby"
```

A markdown response is its own alternate, so it carries the `describedby`
relation only.

The `describedby` target is resolved against your URLconf. An `llms.txt`
file covers the pages under its own path, and the most specific file wins:
a request for `/docs/intro` points at `/docs/llms.txt` when that route
exists, and falls back to `/llms.txt`. No setting lists the location.

Set `LINK_HEADERS` to `False` to turn the header off.

Some clients read markup only. For those, render the same two relations as
HTML `<link>` elements in your `<head>`:

```html
{% load llmstxt %}
<head>
  {% llms_links %}
</head>
```

The tag needs `django.template.context_processors.request` in your template
`OPTIONS`. It renders nothing without a request.

## Detecting markdown requests: `request.markdown`

The middleware attaches a `request.markdown` object (a `MarkdownDetails`) to
every request, in the spirit of [django-htmx][htmx]'s `request.htmx`. It is
**truthy** when the request opted into a markdown representation, so views and
later middleware can branch on it:

```python
def home(request):
    if request.markdown:
        # this request will be served markdown — skip the expensive
        # HTML-only widget that would just be stripped anyway
        ...
```

Two booleans record *how* the request opted in:

| Attribute            | True when                                            |
| -------------------- | ---------------------------------------------------- |
| `request.markdown.via_suffix` | the URL ended in `.md` (a twin)             |
| `request.markdown.via_accept` | negotiated via `Accept: text/markdown`      |

You don't need this to serve markdown — conversion happens transparently in
`process_response` whether or not your view looks at `request.markdown`. It's
for views that want to *proactively* adapt: render a lighter template, set
[`response.llms_md`](#per-page-override-llms_md) dynamically, or log markdown
hits.

[htmx]: https://django-htmx.readthedocs.io/en/latest/middleware.html

## Conversion rules

The response is converted only when **all** hold:

1. The request opted in (`.md` suffix or Accept header)
2. Status 200, not streaming
3. `Content-Type` contains `text/html`
4. The path passes [`INCLUDE`/`EXCLUDE` globs](settings.md) — `EXCLUDE`
   wins, and an excluded route is served its original HTML

Default conversion strips `script`, `style`, `noscript`, and `template`
tags, then converts with ATX headings and `-` bullets. Swap in your own via
[`LLMSTXT["CONVERTER"]`](settings.md).

## Per-page override: `llms_md`

Pages whose HTML converts poorly — app-like pages, heavy tables, canvas
widgets — ship hand-written markdown instead. Checked in order:

```python
# 1. On the response instance (set inside a view)
response["x"] = None  # any view code: response.llms_md = "..."
response.llms_md = "# Handbook\n\nHand-written."


# 2. On a function view, as an attribute
def handbook(request): ...


handbook.llms_md = "# Handbook\n\nHand-written."


# 3. On a CBV, as a class attribute
class HandbookView(TemplateView):
    llms_md = "# Handbook\n\nHand-written."
```

A callable value is called with the request:

```python
def render_handbook_md(request):
    return f"# Handbook\n\nFor {request.user}."


handbook.llms_md = render_handbook_md
```

An override applies everywhere the page is represented as markdown: the
`.md` twin and Accept negotiation.

## Auth safety

If the request has an authenticated user, the markdown response is sent
with `Cache-Control: private, no-store` — so a shared cache that doesn't
vary on `Cookie` can't hand one visitor's page to the next. Anonymous
responses carry no added cache headers and cache normally.

This is the runtime half of the auth story; the other half is that
[indexes are built from explicit sections](sections.md), so gated pages
never appear in `llms.txt`/`llms-full.txt` unless you list them — and you
can list them [metadata-only](cookbook.md#6-list-a-gated-page-without-publishing-its-content).
