from __future__ import annotations

from django import template
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe

from django_llmstxt.utils import llms_txt_url, markdown_url

register = template.Library()


@register.simple_tag(takes_context=True)
def llms_links(context: template.Context) -> SafeString:
    """
    Render the llms.txt v2 discovery relations as HTML ``<link>`` elements::

        {% load llmstxt %}
        {% llms_links %}

    Put the tag in the ``<head>`` of your base template. It is the HTML form
    of the ``Link:`` header that ``LlmsMarkdownMiddleware`` already sends,
    for clients that read markup only. The tag needs the request in the
    template context.
    """
    request: HttpRequest | None = context.get("request")
    if request is None:
        return mark_safe("")  # noqa: S308
    path = request.path_info
    prefix = request.path.removesuffix(path) if request.path.endswith(path) else ""
    links = [
        format_html(
            '<link rel="alternate" type="text/markdown" href="{}">',
            f"{prefix}{markdown_url(path)}",
        )
    ]
    covering = llms_txt_url(path)
    if covering:
        links.append(
            format_html('<link rel="describedby" href="{}">', f"{prefix}{covering}")
        )
    return mark_safe("\n".join(links))  # noqa: S308
