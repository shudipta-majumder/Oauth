# Generated by Django 5.0.4 on 2024-04-30 09:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth_users", "0004_role_is_active"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="role",
        ),
        migrations.AddField(
            model_name="user",
            name="roles",
            field=models.ManyToManyField(to="auth_users.role"),
        ),
    ]
