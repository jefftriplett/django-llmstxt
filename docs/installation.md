# Installation

## Requirements

- Python 3.10+
- Django 5.2+

## Install

```bash
pip install django-llmstxt
```

This pulls in Django, asgiref, and markdownify (plus BeautifulSoup, which the
default converter uses to strip scripts and styles).

## Add to your project

Two independent pieces — use either or both.

### 1. The indexes (`/llms.txt`, `/llms-full.txt`)

Add `django_llmstxt` to `INSTALLED_APPS` (optional but recommended), declare
one or more [sections](sections.md), and wire the [views](views.md):

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_llmstxt",
]

LLMSTXT = {
    "SITE_TITLE": "Acme",
    "SITE_DESCRIPTION": "Payments infrastructure for platforms.",
}
```

```python
# urls.py
from django.urls import path
from django_llmstxt.views import LlmsFullTxtView, LlmsTxtView
from myapp.llms import DocsSection

urlpatterns = [
    path("llms.txt", LlmsTxtView.as_view(sections={"docs": DocsSection})),
    path("llms-full.txt", LlmsFullTxtView.as_view(sections={"docs": DocsSection})),
]
```

### 2. The markdown middleware (`.md` twins, content negotiation)

```python
# settings.py
MIDDLEWARE = [
    # ...
    "django_llmstxt.middleware.LlmsMarkdownMiddleware",
]
```

Placement notes:

- Put it **after** `SessionMiddleware`/`AuthenticationMiddleware` if you want
  authenticated renders to be marked `Cache-Control: private, no-store`
  (recommended).
- Put it **before** `FlatpageFallbackMiddleware` — flat pages are resolved by
  that middleware, and django-llmstxt must rewrite `.md` paths first so the
  fallback can find the page.
- GZipMiddleware ordering doesn't matter; markdown responses are ordinary
  `HttpResponse` objects and get compressed like anything else.

### Verify

```bash
curl http://127.0.0.1:8000/llms.txt
curl http://127.0.0.1:8000/about.md
curl -H "Accept: text/markdown" http://127.0.0.1:8000/about/
```

See the runnable [example project](../example/) for a full working setup.
