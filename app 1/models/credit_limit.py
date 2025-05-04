import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _

from auth_users.models import User
from core.constants import StatusChoices
from core.mixins import AuditLogMixin
from pms.constants import PMSRecommendationStages
from recommendation_engine.models import (
    ApprovalQueue,
    RecommendationProcess,
    RecommendationSystem,
)

__all__ = ["OrgTypeChoices", "CreditLimit", "CreditLimitDetail", "EbsCollectionDetail"]


class OrgTypeChoices(models.TextChoices):
    WDC = "wdc", _("WDC")
    WCL = "wcl", _("WCL")


class ApprovedDayRangeChoices(models.TextChoices):
    COD = "cod", _("COD")
    DAYS_7 = "7_days", _("7 Days")
    DAYS_15 = "15_days", _("15 Days")
    DAYS_30 = "30_days", _("30 Days")


class CreditLimit(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    witp_code = models.CharField(max_length=255, null=True, blank=True)
    party_name = models.CharField(max_length=255, null=True, blank=True)

    approved_range = models.CharField(
        choices=ApprovedDayRangeChoices.choices,
        default=None,
        null=True,
        blank=True,
        verbose_name="Limit Application approved for",
        max_length=88,
        help_text="Credit Monitoring Approval Field !",
    )

    proposed_limit_wdc = models.DecimalField(
        verbose_name="Proposed Limit WDC",
        null=True,
        blank=True,
        max_digits=34,
        decimal_places=2,
    )
    proposed_limit_wcl = models.DecimalField(
        verbose_name="Proposed Limit WCL",
        null=True,
        blank=True,
        max_digits=34,
        decimal_places=2,
    )
    approved_limit_wdc = models.DecimalField(
        verbose_name="Approved Limit WDC",
        null=True,
        blank=True,
        max_digits=34,
        decimal_places=2,
    )
    approved_limit_wcl = models.DecimalField(
        verbose_name="Approved Limit WCL",
        null=True,
        blank=True,
        max_digits=34,
        decimal_places=2,
    )

    wo_po_mou = models.FileField(
        verbose_name="WO/PO/NOA/RFQ/MOU",
        upload_to="credit_limit_applications/",
        null=True,
        blank=True,
    )

    rating_certificate = models.FileField(
        verbose_name="Rating Certificate",
        null=True,
        blank=True,
        upload_to="credit_limit_applications/",
    )

    updated_ledger_wdc = models.FileField(
        verbose_name="Updated Ledger WDC",
        null=True,
        blank=True,
        upload_to="credit_limit_applications/",
    )

    updated_ledger_wcl = models.FileField(
        verbose_name="Updated Ledger WCL",
        null=True,
        blank=True,
        upload_to="credit_limit_applications/",
    )

    judicial_stamp = models.FileField(
        verbose_name="Judicial Stamp",
        null=True,
        blank=True,
        upload_to="credit_limit_applications/",
    )

    grade = models.CharField(
        verbose_name="Grade",
        null=True,
        blank=True,
        max_length=25,
    )

    invoice_due_max_days = models.IntegerField(default=99999999)

    party_address = models.CharField(
        verbose_name="Party Address", max_length=255, null=True, blank=True
    )

    party_status = models.CharField(
        verbose_name="Party Status", max_length=255, null=True, blank=True
    )

    ebs_info_pulled = models.BooleanField(default=False)

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
        default=StatusChoices.INIT,
    )
    remarks = models.CharField(null=True, blank=True, max_length=500)

    system = models.ForeignKey(RecommendationSystem, on_delete=models.DO_NOTHING)
    process = models.ForeignKey(RecommendationProcess, on_delete=models.DO_NOTHING)
    approval_queues = GenericRelation(ApprovalQueue)

    def __str__(self) -> str:
        return f"{self.witp_code} - {self.party_name}"

    @classmethod
    def get_pending_applications(cls, queryset, current_user: User):
        role = current_user.groups.first()
        if not role:
            qs = queryset.filter(
                models.Q(status=StatusChoices.PENDING)
                | models.Q(status=StatusChoices.PROCESSING)
            ).order_by("-created_at")
        else:
            qs = queryset.filter(
                models.Q(status=StatusChoices.PENDING),
                stage__iexact=role.name,
                approval_queues__status=StatusChoices.PENDING,
                approval_queues__node__user=current_user,
            ).distinct()
        return qs

    @classmethod
    def get_approved_applications(cls, queryset, current_user: User):
        role = current_user.groups.first()
        if not role:
            qs = queryset.filter(status=StatusChoices.APPROVED).order_by("-created_at")
        else:
            qs = queryset.filter(
                models.Q(stage=StatusChoices.APPROVED)
                | (
                    models.Q(status=StatusChoices.PENDING)
                    & models.Q(approval_queues__status=StatusChoices.APPROVED)
                    & models.Q(approval_queues__node__user=current_user)
                )
            ).distinct()
        return qs

    @classmethod
    def get_rejected_applications(cls, queryset, current_user: User | None = None):
        if current_user:
            return queryset.filter(
                status=StatusChoices.REJECTED, created_by=current_user
            ).order_by("-created_at")
        return queryset.filter(status=StatusChoices.REJECTED).order_by("-created_at")

    @classmethod
    def get_draft_applications(cls, queryset, current_user: User | None = None):
        if current_user:
            return queryset.filter(status=StatusChoices.DRAFT, created_by=current_user)
        return queryset.filter(status=StatusChoices.DRAFT).order_by("-created_at")

    @classmethod
    def get_all_applications(cls, queryset, current_user: User):
        role = current_user.groups.first()
        if role:
            return queryset.filter(
                (
                    models.Q(stage=StatusChoices.APPROVED)
                    | models.Q(stage=StatusChoices.REJECTED)
                    | (
                        models.Q(stage__iexact=role.name)
                        & models.Q(approval_queues__status=StatusChoices.PENDING)
                        & models.Q(approval_queues__node__user=current_user)
                    )
                    | (
                        models.Q(status=StatusChoices.PENDING)
                        & models.Q(approval_queues__status=StatusChoices.APPROVED)
                        & models.Q(approval_queues__node__user=current_user)
                    )
                ),
            ).distinct()
        return queryset

    @classmethod
    def filter_by_text(cls, queryset, text_param: str):
        return queryset.filter(
            models.Q(id__iexact=text_param)
            | models.Q(witp_code__iexact=text_param)
            | models.Q(party_name__icontains=text_param)
        )

    @classmethod
    def filter_by_created_on_range(cls, queryset, start: str, end: str):
        start_datetime = cls._parse_date_str(start)
        end_datetime = cls._parse_date_str(end)
        return queryset.filter(created_at__date__range=(start_datetime, end_datetime))

    @classmethod
    def filter_by_status(cls, queryset, status: str, current_user: User):
        match status:
            case StatusChoices.PENDING:
                return cls.get_pending_applications(queryset, current_user)
            case StatusChoices.APPROVED:
                return cls.get_approved_applications(queryset, current_user)
            case StatusChoices.REJECTED:
                return cls.get_rejected_applications(queryset)
            case StatusChoices.DRAFT:
                return cls.get_draft_applications(queryset, current_user)
            case _:
                return cls.get_all_applications(queryset, current_user)

    class Meta:
        db_table = "pms_credit_limit_application"
        verbose_name = "Credit Limit Application"
        verbose_name_plural = "📤 Credit Limit Applications"


class CreditLimitDetail(models.Model):
    org_type = models.CharField(
        max_length=30,
        choices=OrgTypeChoices.choices,
        default=None,
        blank=True,
        null=True,
    )
    amount = models.DecimalField(
        max_digits=34,
        decimal_places=2,
    )

    micr_cheque = models.FileField(
        verbose_name="MICR Cheque",
        null=True,
        blank=True,
        upload_to="credit_limit_applications/",
    )

    credit_limit = models.ForeignKey(CreditLimit, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.pk} - {self.org_type} - {self.amount}"

    class Meta:
        db_table = "pms_credit_limit_application_detail"
        verbose_name = "Credit Limit Application Detail"
        verbose_name_plural = "📤 Credit Limit Application Details"


class EbsCollectionDetail(models.Model):
    org_id = models.CharField(max_length=88)
    party_id = models.CharField(max_length=88)
    account_number = models.CharField(max_length=88)
    org_type = models.CharField(max_length=88)
    average_coll_ratio = models.FloatField(default=0.0)
    avg_receipt_amount = models.DecimalField(
        max_digits=34, decimal_places=2, default=0.0
    )
    avg_sale_amount = models.DecimalField(max_digits=34, decimal_places=2, default=0.0)
    last_sale_date = models.DateTimeField(null=True, blank=True)
    last_receipt_date = models.DateTimeField(null=True, blank=True)
    opening_amount = models.DecimalField(max_digits=34, decimal_places=2, default=0.0)
    closing_balance = models.DecimalField(max_digits=34, decimal_places=2, default=0.0)
    total_sales_amount = models.DecimalField(
        max_digits=34, decimal_places=2, default=0.0
    )
    total_receipt_amount = models.DecimalField(
        max_digits=34, decimal_places=2, default=0.0
    )

    credit_limit = models.ForeignKey(
        CreditLimit, on_delete=models.CASCADE, related_name="collection_details"
    )

    def __str__(self) -> str:
        return f"{self.pk} - {self.org_type}"

    class Meta:
        db_table = "pms_ebs_collection_detail"
        verbose_name = "EBS Collection Detail"
        verbose_name_plural = "📤 EBS Collection Details"
