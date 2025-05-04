import uuid

from django.db import models
from django.db.models import CASCADE

from core.mixins import AuditLogMixin

from .tender import Participant, Tender


# This product tabel stores several products of a tender.
class ParticipantBid(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    participant_name = models.ForeignKey(Participant, on_delete=CASCADE)
    biding_price = models.CharField(null=True, blank=True, max_length=100)
    tender = models.ForeignKey(
        Tender, on_delete=CASCADE, related_name="participant_bid"
    )

    def __str__(self):
        return self.participant_name.name
