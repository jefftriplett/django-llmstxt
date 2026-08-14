from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Post",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(unique=True)),
                ("summary", models.CharField(max_length=300)),
                ("body", models.TextField(help_text="Markdown source")),
                ("published", models.BooleanField(default=False)),
                ("pub_date", models.DateTimeField()),
            ],
            options={"ordering": ["-pub_date"]},
        ),
    ]
