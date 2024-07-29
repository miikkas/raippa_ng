# Generated by Django 4.1 on 2024-03-13 12:29

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0005_alter_fileexercisetestincludefile_file_settings_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="term",
            old_name="course",
            new_name="origin",
        ),
        migrations.AlterUniqueTogether(
            name="term",
            unique_together={("origin", "name")},
        ),
        migrations.AddField(
            model_name="calendar",
            name="origin",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="courses.course",
                verbose_name="Course",
            ),
        ),
        migrations.AddField(
            model_name="calendar",
            name="slug",
            field=models.SlugField(
                allow_unicode=True, null=True, max_length=255
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="contentpage",
            name="origin",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="courses.course",
                verbose_name="Course",
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="prefix",
            field=models.CharField(default="null", max_length=4),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="coursemedia",
            name="origin",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="courses.course",
            ),
        ),
        migrations.AddField(
            model_name="coursemedia",
            name="slug",
            field=models.SlugField(
                allow_unicode=True, null=True, max_length=255, unique=True
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="includefilesettings",
            name="export_id",
            field=models.UUIDField(editable=False, unique=True, null=True),
        ),
        migrations.AddField(
            model_name="instanceincludefile",
            name="slug",
            field=models.SlugField(
                allow_unicode=True, null=True, max_length=255, unique=True
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="term",
            name="slug",
            field=models.SlugField(
                allow_unicode=True, null=True, max_length=255, unique=True
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="courseinstance",
            name="slug",
            field=models.SlugField(allow_unicode=True, max_length=255, unique=True),
        ),
    ]
