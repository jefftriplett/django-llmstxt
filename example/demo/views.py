from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Post


def handbook(request: HttpRequest) -> HttpResponse:
    return render(request, "handbook.html")


handbook.llms_md = (
    "# Handbook\n\nHand-written markdown, because the HTML page is app-like.\n"
)


def account(request: HttpRequest) -> HttpResponse:
    return render(request, "account.html")


def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    post = get_object_or_404(Post, slug=slug, published=True)
    return render(request, "post_detail.html", {"post": post})
