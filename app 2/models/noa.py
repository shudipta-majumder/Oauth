import uuid
from logging import getLogger

from django.db import models

from core.mixins import AuditLogMixin

from ..models.tender import Tender

logger = getLogger(__name__)


class NotificationOfAward(models.Model):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    noa_status = models.CharField(
        max_length=100, verbose_name="NOA status", null=True, blank=True
    )
    noa_attachment = models.FileField(upload_to="noa/", null=True, blank=True)
    noa_receiving_date = models.DateField(null=True, blank=True)
    noa_accept_input_day = models.CharField(
        max_length=255, default=0, null=True, blank=True
    )
    noa_acceptance_deadline = models.DateField(null=True, blank=True)
    contract_aggrement_input_day = models.CharField(
        max_length=255, default=0, null=True, blank=True
    )
    contract_agreement_deadline = models.DateField(null=True, blank=True)
    pg_amount = models.CharField(max_length=255, null=True, blank=True)
    pg_issue_date = models.DateField(null=True, blank=True)
    pg_attachment = models.FileField(upload_to="pg/", null=True, blank=True)
    pg_validity_date = models.DateField(null=True, blank=True)
    tender = models.OneToOneField(Tender, on_delete=models.CASCADE, related_name="noa")

    def __str__(self):
        return str(self.id)


class BGReleasedDate(AuditLogMixin):
    date = models.DateField(null=True, blank=True)
    is_bg_released = models.CharField(max_length=100, null=True, blank=True)
    tender = models.ForeignKey(
        Tender, on_delete=models.CASCADE, related_name="bg_released_date"
    )

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
