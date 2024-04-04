# Generated by Django 4.1 on 2024-04-02 15:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0011_fileexercisetestincludefile_export_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contentpage",
            name="origin",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="courses.course",
                verbose_name="Origin course",
            ),
        ),
        migrations.AlterField(
            model_name="course",
            name="prefix",
            field=models.CharField(max_length=4, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name="contentpage",
            unique_together={("name", "origin")},
        ),
    ]
