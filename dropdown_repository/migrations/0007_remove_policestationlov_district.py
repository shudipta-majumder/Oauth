# Generated by Django 5.0.1 on 2024-01-27 11:25

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("dropdown_repository", "0006_policestationlov_phone"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="policestationlov",
            name="district",
        ),
    ]
