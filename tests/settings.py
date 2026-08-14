from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "NOTASECRET"

DEBUG = True

ALLOWED_HOSTS = ["testserver"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

SITE_ID = 1

INSTALLED_APPS = [
    "django.contrib.sites",
    "django.contrib.flatpages",
    "django_llmstxt",
]

MIDDLEWARE = [
    "django_llmstxt.middleware.LlmsMarkdownMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
]

ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "tests" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

USE_TZ = True

LLMSTXT = {
    "SITE_TITLE": "Test Site",
    "SITE_DESCRIPTION": "A site used by the test suite.",
}
