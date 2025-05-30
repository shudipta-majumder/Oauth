# Generated by Django 5.0.6 on 2024-06-25 09:04

from django.db import migrations, models

import pms.models.party_attachment


class Migration(migrations.Migration):
    dependencies = [
        ("pms", "0019_partyattachment_expiry_date_general_attachment_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="party",
            name="ugc_certificate_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="attachments/party",
                verbose_name="UGC Certificate File",
            ),
        ),
        migrations.AddField(
            model_name="party",
            name="ugc_certificate_no",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="UGC Certificate No"
            ),
        ),
        migrations.AddField(
            model_name="partyattachment",
            name="credit_rating_certificate",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=pms.models.party_attachment.upload_to_dir,
                verbose_name="Credit Rating Certificate",
            ),
        ),
    ]
