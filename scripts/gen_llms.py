"""Generate per-page Markdown, llms.txt, and llms-full.txt from a built site.

Zensical has no plugin API yet (https://zensical.org/docs/community/faqs/) and
no llms.txt support, so this runs as a post-build step instead.

Everything here goes through the library itself: pages are converted with
``django_llmstxt.convert.html_to_markdown``, collected into ``LlmsSection``
entries, and rendered by the real ``LlmsTxtView`` / ``LlmsFullTxtView``. The
docs site is therefore the package's own first consumer -- a regression in
the converter or the index format breaks this build before it reaches anyone
else.

This works from the *rendered* HTML rather than docs/*.md on purpose. The docs
use Zensical syntax that means nothing outside the renderer: admonitions
(``!!! note``), grid cards, and content tabs would all reach a reader as raw
markers. Rendering first turns them into prose.

Page order, titles, and URLs come from zensical.toml, so adding a page to the
nav is the only step needed.

Usage: python scripts/gen_llms.py [site_dir]
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib

import django
from bs4 import BeautifulSoup
from django.conf import settings

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = {"404"}


def setup_django(title: str, description: str) -> None:
    """Configure just enough Django to render the views out of process."""
    if not settings.configured:
        settings.configure(
            ALLOWED_HOSTS=["*"],
            DATABASES={},
            INSTALLED_APPS=["django_llmstxt"],
            LLMSTXT={"SITE_TITLE": title, "SITE_DESCRIPTION": description},
        )
        django.setup()


def config() -> dict:
    return tomllib.loads((ROOT / "zensical.toml").read_text())["project"]


def site_url(project: dict) -> str:
    """Canonical base URL, overridable so a preview build self-references."""
    return os.environ.get("SITE_URL", project.get("site_url", "")).rstrip("/")


def nav_order(project: dict) -> list[str]:
    """Page slugs in the order the nav declares them, sections flattened."""

    def walk(entries: list) -> list[str]:
        slugs = []
        for entry in entries:
            values = entry.values() if isinstance(entry, dict) else [entry]
            for value in values:
                if isinstance(value, list):  # a section: {"Cookbooks": [...]}
                    slugs += walk(value)
                else:
                    slugs.append(pathlib.PurePosixPath(value).stem)
        return slugs

    return walk(project.get("nav", []))


def prune(article: BeautifulSoup) -> None:
    """Strip page furniture the Markdown twin should not carry.

    In-page ``<nav>`` and the paragraph-mark permalink anchors are navigation,
    not content, and inline ``<svg>`` is decoration (twemoji icons) that would
    reach a reader as a screenful of path data.

    Highlighted code is the fiddly part. Zensical wraps each block in
    ``<div class="language-python highlight">`` and fills the ``<pre>`` with
    per-token ``<span>`` elements and one empty ``<a>`` line anchor per line;
    converted naively those anchors become ``[]()`` litter inside the fence.
    Flattening the ``<pre>`` to its text and moving the language onto the
    ``<code>`` gives the converter an ordinary fenced block to work with.
    """
    for tag in article.select("nav, svg"):
        tag.decompose()
    for anchor in article.select("a.headerlink"):
        anchor.decompose()

    for block in article.select("div.highlight"):
        pre = block.find("pre")
        if pre is None:
            continue
        language = ""
        for name in block.get("class", []):
            if name.startswith("language-"):
                language = name
        code = BeautifulSoup("", "html.parser").new_tag("code")
        if language:
            code["class"] = [language]
        code.string = pre.get_text()
        pre.clear()
        pre.append(code)
        block.replace_with(pre.extract())


def convert(html: str) -> tuple[str | None, str]:
    """One rendered page as (title, markdown).

    The title is the first ``<h1>``, and the body is everything inside
    ``<article>``. A page without an article converts to nothing.
    """
    from django_llmstxt.conf import app_settings

    article = BeautifulSoup(html, "html.parser").find("article")
    if article is None:
        return None, ""
    prune(article)
    heading = article.find("h1")
    title = re.sub(r"\s+", " ", heading.get_text()).strip() if heading else None
    return title, app_settings.CONVERTER(str(article))


def summarize(markdown: str) -> str:
    """The page's first real paragraph, flattened to one line of plain text.

    Taken from the page itself rather than a separate description field, so a
    description cannot go stale while the page changes underneath it.
    """
    body = re.sub(r"^#.*$", "", markdown, count=1, flags=re.MULTILINE)
    for block in body.split("\n\n"):
        block = block.strip()
        if not block or block.startswith(("#", "```", "|", "<", "-", "*", ">")):
            continue
        text = " ".join(block.split())
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links to their text
        text = re.sub(r"[`*_]", "", text)
        return text
    return ""


def slug_of(page: pathlib.Path, site: pathlib.Path) -> str:
    rel = page.relative_to(site)
    return "index" if rel.parent == pathlib.Path(".") else rel.parent.as_posix()


def extract(site: pathlib.Path) -> dict[str, tuple[str, str]]:
    """Every rendered page, as {slug: (title, markdown)}."""
    pages = {}
    for html_file in sorted(site.rglob("index.html")):
        slug = slug_of(html_file, site)
        if slug in SKIP:
            continue
        title, body = convert(html_file.read_text(encoding="utf-8"))
        pages[slug] = (title or slug, body)
    return pages


def render(entries: list, base_url: str) -> tuple[str, str]:
    """llms.txt and llms-full.txt, rendered by the package's own views."""
    from django.test import RequestFactory

    from django_llmstxt.sections import LlmsSection
    from django_llmstxt.views import LlmsFullTxtView, LlmsTxtView

    class DocsSection(LlmsSection):
        title = "Docs"

        def items(self):
            return entries

    request = RequestFactory().get("/llms.txt")
    sections = {"docs": DocsSection}
    index = LlmsTxtView.as_view(sections=sections)(request)
    full = LlmsFullTxtView.as_view(sections=sections)(request)
    return index.content.decode(), full.content.decode()


def main() -> int:
    site = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    if not site.is_dir():
        print(f"error: {site} does not exist -- build the site first", file=sys.stderr)
        return 1

    project = config()
    base_url = site_url(project)
    setup_django(project["site_name"], project["site_description"])

    from django_llmstxt.sections import LlmsEntry

    pages = extract(site)
    # The nav is the running order; anything it does not list is appended
    # alphabetically, so a new page still shows up without editing the nav.
    ordered = [slug for slug in nav_order(project) if slug in pages]
    ordered += sorted(set(pages) - set(ordered))

    entries = []
    for slug in ordered:
        title, body = pages[slug]
        # A Markdown twin next to every page: /views/ -> /views.md
        md_path = site / ("index.md" if slug == "index" else f"{slug}.md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(body, encoding="utf-8")

        url = f"{base_url}/" if slug == "index" else f"{base_url}/{slug}.md"
        entries.append(
            LlmsEntry(
                title=title,
                url=url,
                description=summarize(body),
                content=body,
            )
        )

    index, full = render(entries, base_url)
    (site / "llms.txt").write_text(index, encoding="utf-8")
    (site / "llms-full.txt").write_text(full, encoding="utf-8")

    words = len(full.split())
    print(
        f"wrote llms.txt ({len(entries)} pages), "
        f"llms-full.txt (~{words:,} words), and {len(entries)} .md twins"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
