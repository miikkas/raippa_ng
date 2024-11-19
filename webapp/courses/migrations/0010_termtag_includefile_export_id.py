# Generated by Django 4.1 on 2024-03-14 14:07

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0009_finalize_slugfields"),
    ]

    operations = [
        migrations.AddField(
            model_name="termtag",
            name="export_id",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="fileexercisetestincludefile",
            name="export_id",
            field=models.UUIDField(editable=False, null=True),
        ),
    ]
