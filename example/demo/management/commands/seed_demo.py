from __future__ import annotations

from datetime import timedelta

from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.utils import timezone

from demo.models import Post


class Command(BaseCommand):
    help = "Create example posts and flat pages."

    def handle(self, *args, **options):
        now = timezone.now()
        posts = [
            {
                "title": "Welcome to Example Corp",
                "slug": "welcome",
                "summary": "Meet the tiny site behind this package demo.",
                "body": "# Welcome\n\nThis post is stored as **Markdown** source.",
                "published": True,
                "pub_date": now - timedelta(days=3),
            },
            {
                "title": "Markdown for every page",
                "slug": "markdown-for-every-page",
                "summary": "Serve useful Markdown alongside ordinary HTML.",
                "body": "# Markdown for every page\n\nRequest a `.md` twin or negotiate with `Accept`.",
                "published": True,
                "pub_date": now - timedelta(days=2),
            },
            {
                "title": "Building an llms.txt index",
                "slug": "building-an-llms-index",
                "summary": "Organize discoverable content into sections.",
                "body": "# Building an llms.txt index\n\nSections make public content easy to discover.",
                "published": True,
                "pub_date": now - timedelta(days=1),
            },
            {
                "title": "Next quarter preview",
                "slug": "next-quarter-preview",
                "summary": "An unpublished post that stays out of public surfaces.",
                "body": "# Next quarter\n\nThis draft must not appear in the index.",
                "published": False,
                "pub_date": now,
            },
        ]
        for post_data in posts:
            _, created = Post.objects.get_or_create(
                slug=post_data["slug"], defaults=post_data
            )
            self.stdout.write(
                f"{'Created' if created else 'Already exists'} post: {post_data['title']}"
            )

        site = Site.objects.get_current()
        pages = [
            (
                "/about/",
                "About Example Corp",
                "<h1>About Example Corp</h1><p>We build small, useful demonstrations.</p>",
            ),
            (
                "/legal/",
                "Legal",
                "<h1>Legal</h1><p>This example is provided for demonstration purposes.</p>",
            ),
        ]
        for url, title, content in pages:
            page, created = FlatPage.objects.get_or_create(
                url=url, defaults={"title": title, "content": content}
            )
            page.sites.add(site)
            self.stdout.write(
                f"{'Created' if created else 'Already exists'} flat page: {title}"
            )
