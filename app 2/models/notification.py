import uuid

from django.db import models
from django.utils import timezone

from .tender import Tender


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("BG", "BG"),
        ("PG", "PG"),
        ("NOA ACCEPTANCE DEADLINE", "NOA ACCEPTANCE DEADLINE"),
        ("CONTRACT AGREEMENT DEADLINE", "CONTRACT AGREEMENT DEADLINE"),
        ("COMPLETION CERTIFICATE", "COMPLETION CERTIFICATE"),
        ("DELIVERY DEADLINE", "DELIVERY DEADLINE"),
    )

    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE)
    tender_id_ref = models.CharField(max_length=100, blank=True, null=None)
    team_name = models.CharField(max_length=255, blank=True, null=True)
    tender_type = models.CharField(max_length=255, blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    remaining_time = models.DurationField(blank=True, null=True)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    procurring_entity = models.CharField(max_length=255, blank=True, null=True)
    kam_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification for Tender ID: {self.tender.tender_id} - {self.get_notification_type_display()}"

    def save(self, *args, **kwargs):
        self.remaining_time = self.deadline - timezone.now().date()
        if self.tender and self.tender.team_name:
            self.team_name = self.tender.team_name.team_name
            self.tender_type = self.tender.tender_type.type_name
        super().save(*args, **kwargs)
