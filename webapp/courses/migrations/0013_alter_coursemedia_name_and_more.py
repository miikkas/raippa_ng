# Generated by Django 4.1 on 2024-05-13 14:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0012_alter_contentpage_origin_alter_course_prefix_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coursemedia",
            name="name",
            field=models.CharField(
                max_length=200, verbose_name="Unique name identifier"
            ),
        ),
        migrations.AlterField(
            model_name="includefilesettings",
            name="chmod_settings",
            field=models.CharField(
                default="rw-rw-r--", max_length=10, verbose_name="File access mode"
            ),
        ),
    ]
