from __future__ import annotations

from django_llmstxt import validate_llmstxt


class TestValidateLlmstxt:
    def test_minimal_valid_file(self):
        assert validate_llmstxt("# Acme\n") == []

    def test_full_valid_file(self):
        text = (
            "# Acme\n\n"
            "> Payments for platforms.\n\n"
            "Start with the quickstart.\n\n"
            "## Docs\n\n"
            "- [Getting started](https://example.com/docs/start/): Install.\n"
        )
        assert validate_llmstxt(text) == []

    def test_empty_file(self):
        (issue,) = validate_llmstxt("\n\n   \n")
        assert "empty file" in issue

    def test_missing_h1(self):
        (issue,) = validate_llmstxt("> Just a blockquote.\n")
        assert "must open with an H1" in issue

    def test_bullet_without_a_link(self):
        (issue,) = validate_llmstxt("# Acme\n\n## Docs\n\n- Getting started\n")
        assert "not a markdown link" in issue
        assert "line 5" in issue

    def test_multiple_h1(self):
        issues = validate_llmstxt("# Acme\n\n# Also Acme\n")
        assert any("exactly one H1" in issue for issue in issues)

    def test_ignores_content_inside_code_fences(self):
        text = (
            "# Acme\n\n"
            "```python\n"
            "# not a heading\n"
            "- not a bullet link\n"
            "```\n\n"
            "## Docs\n\n"
            "- [Start](https://example.com/): Go.\n"
        )
        assert validate_llmstxt(text) == []

    def test_tolerates_a_bom(self):
        assert validate_llmstxt("﻿# Acme\n") == []
