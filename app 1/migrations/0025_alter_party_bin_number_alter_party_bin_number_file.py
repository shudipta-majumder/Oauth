# Generated by Django 5.0.6 on 2024-06-27 09:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pms", "0024_alter_creditlimit_stage_alter_party_stage_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="party",
            name="bin_number",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="VAT/BIN Number"
            ),
        ),
        migrations.AlterField(
            model_name="party",
            name="bin_number_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="attachments/party",
                verbose_name="Business Identification Numbers",
            ),
        ),
    ]
