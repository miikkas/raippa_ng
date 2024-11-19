# Generated by Django 5.0.6 on 2024-08-19 11:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0018_about"),
    ]

    operations = [
        migrations.AlterField(
            model_name="courseinstance",
            name="name",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="courseinstance",
            name="name_en",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="courseinstance",
            name="name_fi",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
