# Generated by Django 5.0.6 on 2024-08-12 15:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0017_finalize_ordinals"),
    ]

    operations = [
        migrations.CreateModel(
            name="About",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("content", models.TextField(blank=True, null=True)),
                ("content_en", models.TextField(blank=True, null=True)),
                ("content_fi", models.TextField(blank=True, null=True)),
            ],
        ),
    ]
