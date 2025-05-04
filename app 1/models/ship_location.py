import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from core.constants import StatusChoices
from core.mixins import AuditLogMixin
from pms.constants import PMSRecommendationStages
from pms.models.party import DistanceTypeChoices
from recommendation_engine.models import (
    ApprovalQueue,
    RecommendationProcess,
    RecommendationSystem,
)

__all__ = ["ShipLocation"]


class ShipLocation(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    witp_code = models.CharField(max_length=255)
    party_name = models.CharField(max_length=255)
    recommended_delivery_addr = models.CharField(
        verbose_name="Recommended Delivery Address",
        max_length=500,
    )
    receiver_name = models.CharField(verbose_name="Receiver Name", max_length=255)
    receiver_number = models.CharField(verbose_name="Receiver Number", max_length=20)
    factory_distance = models.CharField(
        verbose_name="Factory Distance",
        choices=DistanceTypeChoices.choices,
        max_length=255,
    )
    marketing_concern = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    wo_po_mou_reference = models.CharField(
        verbose_name="WO/PO/NOA/RFQ/MOU/Any Reference",
        max_length=255,
    )
    authorization_letter = models.CharField(
        verbose_name="Authorization Letter",
        max_length=255,
        null=True,
        blank=True,
    )
    wo_po_mou_attachment = models.FileField(
        verbose_name="WO/PO/NOA/RFQ/MOU",
        null=True,
        blank=True,
        upload_to="ship_location_applications/",
    )

    authorization_letter_attachment = models.FileField(
        verbose_name="Authorization Letter / Any Reference",
        null=True,
        blank=True,
        upload_to="ship_location_applications/",
    )

    default_addr = models.CharField(max_length=255, null=True, blank=True)

    stage = models.CharField(
        max_length=255,
        choices=PMSRecommendationStages.choices,
        default=None,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=255,
        choices=StatusChoices.choices,
        default=StatusChoices.SUBMITTED,
    )

    system = models.ForeignKey(RecommendationSystem, on_delete=models.DO_NOTHING)
    process = models.ForeignKey(RecommendationProcess, on_delete=models.DO_NOTHING)
    approval_queues = GenericRelation(ApprovalQueue)

    def __str__(self) -> str:
        return f"{self.witp_code} - {self.party_name}"

    class Meta:
        db_table = "pms_ship_location_application"
        verbose_name = "Ship Location Application"
        verbose_name_plural = "🚢 Ship Location Applications"
