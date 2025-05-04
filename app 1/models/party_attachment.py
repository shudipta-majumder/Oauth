import os

from django.db import models
from django.utils.translation import gettext_lazy as _

from . import Party

__all__ = ["PartyAttachment", "AttachmentRepository", "ExtraAttachment"]


def upload_to_dir(instance: "PartyAttachment", file_name):
    return os.path.join(
        "attachments", str(instance.party.id), f"{str(instance.party.id)}_{file_name}"
    )


class AttachmentRepository(models.Model):
    class AllowedExtension(models.TextChoices):
        IMAGE = "image", _("IMAGE")
        PDF = "pdf", _("PDF")
        ANY = "any", _("ANY")

    codename = models.CharField(verbose_name="Code Name", max_length=255)
    viewname = models.CharField(verbose_name="View Name", max_length=255)
    is_active = models.BooleanField(verbose_name="Is Active ?", default=True)
    parent_id = models.IntegerField(
        verbose_name="Parent ID", null=True, blank=True, default=None
    )

    extension = models.CharField(
        max_length=255,
        verbose_name="Extension",
        choices=AllowedExtension.choices,
        default=AllowedExtension.PDF,
    )

    def __str__(self) -> str:
        return self.viewname

    class Meta:
        db_table = "pms_attachment_repository"
        verbose_name = "Attachment Repository"
        verbose_name_plural = "🗃️ Attachment Repositories"


class PartyAttachment(models.Model):
    party_authorization_letter = models.FileField(
        upload_to=upload_to_dir,
        null=True,
        blank=True,
    )
    party_authorization_letter_desc = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    incorporation_certificate = models.FileField(
        upload_to=upload_to_dir, null=True, blank=True
    )
    incorporation_certificate_desc = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    payment_receipt = models.FileField(
        upload_to=upload_to_dir,
        null=True,
        blank=True,
    )
    payment_receipt_desc = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    bank_solvency = models.FileField(upload_to=upload_to_dir, null=True, blank=True)
    bank_solvency_desc = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    security_cheque = models.FileField(upload_to=upload_to_dir, null=True, blank=True)
    security_cheque_desc = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    general_attachment = models.FileField(
        upload_to=upload_to_dir, null=True, blank=True
    )
    expiry_date_general_attachment = models.DateField(
        null=True,
        blank=True,
        verbose_name="Expiry Date for Attachment(If Applicable)",
    )

    credit_rating_certificate = models.FileField(
        null=True,
        blank=True,
        verbose_name="Credit Rating Certificate",
        upload_to=upload_to_dir,
    )

    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="attachments",
    )

    def __str__(self) -> str:
        return str(self.pk)

    class Meta:
        db_table = "pms_party_attachment"
        verbose_name = "Party Attachment"
        verbose_name_plural = "📦 Party Attachment's"


class ExtraAttachment(models.Model):
    desc = models.CharField(
        max_length=255,
    )
    file = models.FileField(upload_to=upload_to_dir)

    is_existing = models.BooleanField(default=True)

    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="extras")

    def __str__(self) -> str:
        return str(self.desc)

    class Meta:
        db_table = "pms_extra_attachments"
        verbose_name = "Extra Attachment"
        verbose_name_plural = "Extra Attachments"
