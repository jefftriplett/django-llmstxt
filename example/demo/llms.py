from __future__ import annotations

from django_llmstxt import LlmsSection

from .models import Post


class RootSection(LlmsSection):
    title = None

    def items(self):
        return [
            {
                "title": "Home",
                "url": "/",
                "description": "Example Corp's demo home page.",
                "content": "# Example Corp\n\nA small site demonstrating django-llmstxt.",
            },
            {
                "title": "Pricing",
                "url": "/pricing/",
                "description": "Simple plans for teams of every size.",
                "content": "# Pricing\n\nStarter is free. Pro is $29 per month.",
            },
            {
                "title": "Your account",
                "url": "/account/",
                "description": "Billing and settings. Requires sign-in.",
            },
        ]


class BlogSection(LlmsSection):
    title = "Blog"

    def items(self):
        return Post.objects.filter(published=True)

    def item_title(self, item: Post) -> str:
        return item.title

    def item_description(self, item: Post) -> str:
        return item.summary

    def item_content(self, item: Post) -> str:
        return item.body

    def item_url(self, item: Post) -> str:
        return item.get_absolute_url()
