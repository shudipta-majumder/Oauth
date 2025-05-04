from django.db.models import CharField, DateField

from core.mixins import AuditLogMixin

__all__ = [
    "BaseParty",
]


class BaseParty(AuditLogMixin):
    witp_code = CharField("WITP Code", max_length=255, null=True, blank=True)

    party_name = CharField(
        verbose_name="Party Name", max_length=255, null=False, blank=False
    )
    owner_name = CharField(
        verbose_name="Owner Name", max_length=99, null=False, blank=False
    )

    trade_license_expires = DateField("Trade License Expires", null=True, blank=True)

    class Meta:
        abstract = True
