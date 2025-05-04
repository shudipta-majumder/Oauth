from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from core.constants import StatusChoices
from core.mixins import AuditLogMixin


class RecommendationSystem(AuditLogMixin):
    """Dynamically define the systems that requires to use the Recommendation Engine"""

    codename = models.CharField(
        verbose_name="Code Name",
        null=False,
        blank=False,
        max_length=88,
        primary_key=True,
    )
    viewname = models.CharField(
        verbose_name="View Name", null=False, blank=False, max_length=255
    )
    description = models.TextField(verbose_name="Description", null=True, blank=True)

    class Meta:
        verbose_name_plural = "Recommendation Systems"
        verbose_name = "Recommendation System"

    def __str__(self) -> str:
        return str(self.viewname)


class RecommendationProcess(AuditLogMixin):
    codename = models.CharField(
        verbose_name="Code Name",
        null=False,
        blank=False,
        max_length=88,
        primary_key=True,
    )
    viewname = models.CharField(
        verbose_name="View Name", null=False, blank=False, max_length=255
    )
    system = models.ForeignKey(
        RecommendationSystem,
        verbose_name="Recommendation System",
        to_field="codename",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name_plural = "Recommendation Processes"
        verbose_name = "Recommendation Process"

    def __str__(self) -> str:
        return str(self.viewname)


class ApprovalStep(AuditLogMixin):
    system = models.ForeignKey(RecommendationSystem, on_delete=models.CASCADE)
    process = models.ForeignKey(RecommendationProcess, on_delete=models.CASCADE)
    codename = models.CharField("Code Name", max_length=255)
    forward_step = models.IntegerField("Forward Step")
    backward_step = models.IntegerField("Backward Step")
    remarks = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Approval Step"
        verbose_name_plural = "Approval Steps"

    def __str__(self) -> str:
        return f"{self.system} | {self.process} | {self.codename}"


class ApprovalUser(AuditLogMixin):
    approval_step = models.ForeignKey(ApprovalStep, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    @classmethod
    def get_path_for(cls, system, process):
        """
        Retrieves active ApprovalUser instances based on the given system and process.

        Args:
            system: The system to filter approval steps by.
            process: The process to filter approval steps by.

        Returns:
            QuerySet of active ApprovalUser instances matching the criteria.
        """
        return cls.objects.select_related("approval_step").filter(
            approval_step__system=system,
            approval_step__process=process,
            is_active=True,
        )

    class Meta:
        verbose_name = "Recommender User"
        verbose_name_plural = "Recommender User Nodes"
        ordering = ("approval_step__forward_step",)

    def __str__(self) -> str:
        return f"{self.user} | System={self.approval_step}"


class ApprovalQueue(AuditLogMixin):
    node = models.ForeignKey(ApprovalUser, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    remarks = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=255, choices=StatusChoices.choices, default=StatusChoices.PENDING
    )

    def get_first_pending_node(
        self, status=StatusChoices.PENDING, column: str = "forward_step"
    ):
        """get the first pending node ascending to given column"""
        return (
            ApprovalQueue.objects.filter(object_id=self.object_id, status=status)
            .order_by(f"node__approval_step__{column}")
            .first()
        )

    def stage_name(self) -> str:
        """get the current node approval step stage name"""
        return self.node.approval_step.codename.lower()

    def get_nodes(self, status=StatusChoices.PENDING, column: str = "forward_step"):
        """get the approval chain for the current instance"""
        return ApprovalQueue.objects.filter(
            object_id=self.object_id, status=status
        ).order_by(f"node__approval_step__{column}")

    def mark_chain_rejected(self, node_ids):
        """update the full chain to rejected where current instance are pending"""
        return ApprovalQueue.objects.filter(
            object_id=self.object_id,
            pk__in=node_ids,
        ).update(status=StatusChoices.REJECTED, updated_at=timezone.now())

    class Meta:
        verbose_name_plural = "Approval Queues"
        verbose_name = "Approval Queue"
        ordering = ("node__approval_step__forward_step",)

    def __str__(self) -> str:
        return f"{self.content_type} | {self.object_id} | {self.stage_name().upper()}"
