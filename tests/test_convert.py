"""The default HTML-to-markdown converter."""

from __future__ import annotations

import pytest

from django_llmstxt.convert import html_to_markdown


def test_headings_use_atx_style():
    assert "## Attributes" in html_to_markdown("<h2>Attributes</h2>")


def test_bullets_use_dashes():
    assert "- One" in html_to_markdown("<ul><li>One</li></ul>")


def test_links_become_markdown():
    assert "[docs](/docs/)" in html_to_markdown('<p><a href="/docs/">docs</a></p>')


@pytest.mark.parametrize("tag", ["script", "style", "noscript", "template"])
def test_non_content_tags_are_dropped(tag):
    out = html_to_markdown(f"<{tag}>secret</{tag}><p>Kept</p>")
    assert "secret" not in out
    assert "Kept" in out


def test_runs_of_blank_lines_collapse():
    assert "\n\n\n" not in html_to_markdown("<p>One</p><br><br><br><p>Two</p>")


# --- fenced code ------------------------------------------------------------


@pytest.mark.parametrize("prefix", ["language", "lang", "highlight"])
def test_code_language_comes_from_the_class(prefix):
    html = f'<pre class="{prefix}-python"><code>x = 1</code></pre>'
    assert "```python" in html_to_markdown(html)


def test_code_language_is_read_from_the_inner_code_element():
    html = '<pre><code class="language-python">x = 1</code></pre>'
    assert "```python" in html_to_markdown(html)


def test_unlabelled_code_gets_a_bare_fence():
    out = html_to_markdown("<pre><code>x = 1</code></pre>")
    assert "```\nx = 1" in out


def test_code_indentation_survives():
    html = '<pre class="language-python"><code>def home():\n    return 1\n</code></pre>'
    assert "    return 1" in html_to_markdown(html)
