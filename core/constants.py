from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

EXCLUDE_FIELDS = ["created_at", "created_by", "updated_at", "updated_by"]


class SystemChoices(models.TextChoices):
    PMS = "party_management_system", _("Party Management System")
    CPQ = "corporate_quotation", _("Corporate Quotation System")


class CustomPermissions:
    INCHARGE_APPROVAL = "has_incharge_approval"
    HOD_APPROVAL = "has_hod_approval"
    ACCOUNT_APPROVAL = "has_account_approval"
    CBO_APPROVAL = "has_cbo_approval"
    AMD_APPROVAL = "has_amd_approval"
    CHAIRMAN_APPROVAL = "has_chairman_approval"


class Groups:
    MEMBER = "Member"
    INCHARGE = "Incharge"
    HOD = "HOD"
    ACCOUNT = "Account"
    CBO = "CBO"
    AMD = "AMD"
    CHAIRMAN = "Chairman"


class StatusChoices(models.TextChoices):
    INIT = "init"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ARCHIVED = "archived"
    PROCESSING = "processing"
    NOT_REQUIRED = "not_required"


class StatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=StatusChoices.choices)
