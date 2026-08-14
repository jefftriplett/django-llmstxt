from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup
from markdownify import markdownify

STRIP_TAGS = ["script", "style", "noscript", "template"]
REPEAT_NEWLINES_RE = re.compile(r"\n{3,}")
LANGUAGE_CLASS_RE = re.compile(r"^(?:language|highlight|lang)-(.+)$")


def code_language(pre: Any) -> str:
    """
    The language of a highlighted block, for the opening fence.

    Highlighters label the block with a class, on the ``<pre>`` itself or on
    the ``<code>`` inside it: ``language-python`` (Pygments, Prism,
    highlight.js), ``lang-python``, or ``highlight-python`` (Sphinx). An
    unlabelled block gets a bare fence.
    """
    for element in (pre, pre.find("code")):
        if element is None:
            continue
        for name in element.get("class", []):
            match = LANGUAGE_CLASS_RE.match(name)
            if match:
                return match.group(1)
    return ""


def html_to_markdown(html: str, *, url: str = "") -> str:
    """
    Default HTML-to-markdown converter.

    Drops non-content tags, converts with ATX headings and ``-`` bullets,
    labels fenced code blocks with their language, and collapses vertical
    whitespace. Swap out via the ``LLMSTXT["CONVERTER"]`` setting.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(STRIP_TAGS):
        tag.decompose()
    markdown = markdownify(
        str(soup),
        heading_style="ATX",
        bullets="-",
        code_language_callback=code_language,
    )
    markdown = REPEAT_NEWLINES_RE.sub("\n\n", markdown)
    return markdown.strip() + "\n"
