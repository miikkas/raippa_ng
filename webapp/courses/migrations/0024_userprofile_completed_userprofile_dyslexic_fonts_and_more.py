# Generated by Django 5.0.6 on 2024-11-27 11:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0023_userprofile_data_policy"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="completed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="dyslexic_fonts",
            field=models.BooleanField(
                default=False,
                verbose_name="Use dyslexic fonts (OpenDyslexic).",
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="data_policy",
            field=models.CharField(
                choices=[
                    ("UNSELECTED", "Not selected"),
                    ("ANONYMIZE", "Institution policy (anonymize)"),
                    ("DELETE", "Institution policy (delete)"),
                    ("RETAIN", "Retain my data"),
                ],
                default="UNSELECTED",
                max_length=10,
                verbose_name="Data retention preference",
            ),
        ),
    ]
