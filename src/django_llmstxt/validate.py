from __future__ import annotations

import re

LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")


def validate_llmstxt(text: str) -> list[str]:
    """
    Check ``text`` against the llms.txt **index** format, returning a list of
    human-readable problems (empty list means it looks well-formed).

    This validates an ``llms.txt`` index, not ``llms-full.txt`` — the latter
    embeds whole page bodies, whose own headings and bullet lists would look
    like violations here.

    The rules mirror the spec's required structure:

    - the file opens with a single H1 title (the only required section);
    - every bullet in a file list is a markdown hyperlink ``[name](url)``.

    Fenced code blocks are ignored, so a code sample in the content section
    does not trip the checks. Use it in a test or a CI step::

        from django.test import Client
        from django_llmstxt.validate import validate_llmstxt

        problems = validate_llmstxt(Client().get("/llms.txt").text)
        assert not problems, problems
    """
    issues: list[str] = []
    lines = text.lstrip("﻿").splitlines()

    content_lines = [line for line in lines if line.strip()]
    if not content_lines:
        return ["empty file: an llms.txt needs at least an H1 title"]

    first = content_lines[0]
    if not first.startswith("# "):
        issues.append(f'must open with an H1 title ("# ..."); found: {first!r}')

    h1_count = 0
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("# "):
            h1_count += 1
        bullet = line.lstrip()
        if (bullet.startswith("- ") or bullet.startswith("* ")) and not LINK_RE.search(
            bullet
        ):
            issues.append(
                f"line {number}: list item is not a markdown link: {line.strip()!r}"
            )

    if h1_count > 1:
        issues.append(f"expected exactly one H1 title, found {h1_count}")

    return issues
