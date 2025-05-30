# Generated by Django 5.0.6 on 2024-08-31 04:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tms", "0020_tender_bg_released_status"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="contractagreement",
            name="earliest_pg_released_date",
        ),
        migrations.RemoveField(
            model_name="contractagreement",
            name="is_pg_released",
        ),
        migrations.RemoveField(
            model_name="contractagreement",
            name="pg_released_date",
        ),
        migrations.AddField(
            model_name="tender",
            name="pg_released_status",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="PGReleasedDate",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField(blank=True, null=True)),
                (
                    "is_pg_released",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_by_%(class)s_related",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "tender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pg_released_date",
                        to="tms.tender",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_by_%(class)s_related",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
