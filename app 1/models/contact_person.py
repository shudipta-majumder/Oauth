from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    EmailField,
    FileField,
    ForeignKey,
    Model,
)

from pms.models import Party

__all__ = ["Contact"]


class Contact(Model):
    name = CharField(
        verbose_name="Authorized Contact Person",
        max_length=99,
        null=False,
        blank=False,
    )
    email = EmailField(verbose_name="Email", null=True, blank=True)
    phone = CharField(verbose_name="Phone", max_length=20, null=False, blank=False)

    party = ForeignKey(
        Party, on_delete=CASCADE, null=False, blank=False, related_name="contacts"
    )

    pp_photo_file = FileField(
        upload_to="attachments/",
        null=True,
        blank=True,
        verbose_name="Passport Size Photo",
    )

    vcard_file = FileField(
        upload_to="attachments/contacts",
        null=True,
        blank=True,
        verbose_name="Visiting Card",
    )
    vcard_number = CharField(
        verbose_name="vCard Number", max_length=20, null=True, blank=True
    )
    ecard_file = FileField(
        upload_to="attachments/contacts",
        null=True,
        blank=True,
        verbose_name="Employee Card",
    )
    ecard_number = CharField(
        verbose_name="EmployeeID Number", max_length=20, null=True, blank=True
    )
    nid_file = FileField(
        upload_to="attachments/contacts",
        null=True,
        blank=True,
        verbose_name="National Identification Card",
    )
    nid_number = CharField(
        verbose_name="NID Number", max_length=20, null=True, blank=True
    )

    is_existing = BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        db_table = "pms_contact_person"
        verbose_name = "Contact Person"
        verbose_name_plural = "📤 Contact Person's"
