# django-llmstxt example

Run the example with the repository's `uv` environment. From the repository root:

```bash
uv sync --group test
uv run python example/manage.py migrate
uv run python example/manage.py seed_demo
uv run python example/manage.py runserver
```

The seed command is idempotent: it creates three published blog posts, one draft, and two Django flat pages. Once the server is running, try each public surface.

## Discoverable indexes

`llms.txt` demonstrates grouped discovery metadata from static dictionaries, Django flat pages, and model instances:

```bash
curl http://127.0.0.1:8000/llms.txt
```

Expected excerpt:

```markdown
# Example Corp

> A demo of django-llmstxt.

- [Home](http://127.0.0.1:8000/): Example Corp's demo home page.
- [Your account](http://127.0.0.1:8000/account/): Billing and settings. Requires sign-in.

## Pages
```

`llms-full.txt` demonstrates bulk content. Published post Markdown and flat-page content appear, while the account entry contains only metadata and a source link:

```bash
curl http://127.0.0.1:8000/llms-full.txt
```

Expected excerpt:

```markdown
### Your account

[Source](http://127.0.0.1:8000/account/)

## Pages
```

## Markdown twins

The flat-page fallback and llms middleware work together: `/about.md` resolves the database-backed `/about/` page and converts its HTML content:

```bash
curl http://127.0.0.1:8000/about.md
```

Expected excerpt:

```markdown
# About Example Corp

We build small, useful demonstrations.
```

Static template views also receive Markdown twins. The semantic table on the pricing page becomes readable Markdown:

```bash
curl http://127.0.0.1:8000/pricing.md
```

Expected excerpt:

```markdown
# Pricing

Choose a plan that grows with your team.
```

The handbook uses a view-level `llms_md` override rather than converting its app-like HTML:

```bash
curl http://127.0.0.1:8000/handbook.md
```

Expected output:

```markdown
# Handbook

Hand-written markdown, because the HTML page is app-like.
```

Content negotiation serves the same Markdown at the canonical URL and adds `Vary: Accept`:

```bash
curl -i -H 'Accept: text/markdown' http://127.0.0.1:8000/pricing/
```

Expected headers and excerpt:

```text
Content-Type: text/markdown; charset=utf-8
Vary: Accept

# Pricing
```
