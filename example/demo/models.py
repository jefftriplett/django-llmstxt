from __future__ import annotations

from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=300)
    body = models.TextField(help_text="Markdown source")
    published = models.BooleanField(default=False)
    pub_date = models.DateTimeField()

    class Meta:
        ordering = ["-pub_date"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return f"/blog/{self.slug}/"
