from typing import Any

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.contenttypes.models import ContentType

from pms.models import (
    Contact,
    CreditLimit,
    CreditLimitDetail,
    EbsCollectionDetail,
    ExtraAttachment,
    Guarantee,
    Party,
    PartyAttachment,
    PartyDealing,
    SecurityCheque,
    ShipLocation,
)
from recommendation_engine.models import ApprovalQueue


class SecurityChequeInline(admin.TabularInline):
    model = SecurityCheque
    extra = 0


class GuarantorInline(admin.TabularInline):
    model = Guarantee
    extra = 0


class DealingInline(admin.StackedInline):
    extra = 0
    model = ExtraAttachment


class ExtraAttachmentInline(admin.TabularInline):
    model = PartyDealing


class ContactPersonsInline(admin.TabularInline):
    model = Contact
    extra = 0


class CreditLimitDetailInline(admin.TabularInline):
    model = CreditLimitDetail
    extra = 0


class EbsCollectionDetailInline(admin.TabularInline):
    model = EbsCollectionDetail
    extra = 0


class AttachmentInline(admin.TabularInline):
    verbose_name_plural = "Attachments"
    show_change_link = True
    model = PartyAttachment
    extra = 0


class ApprovalQueueInline(GenericStackedInline):
    verbose_name_plural = "Approval Queues"
    ct_field = "content_type"
    ct_fk_field = "object_id"
    model = ApprovalQueue
    extra = 0
    exclude = ("created_by", "updated_by")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(content_type=ContentType.objects.get_for_model(Party))


class ApprovalQueueInlineForShipLocation(GenericStackedInline):
    verbose_name_plural = "Approval Queues"
    ct_field = "content_type"
    ct_fk_field = "object_id"
    model = ApprovalQueue
    extra = 0
    exclude = ("created_by", "updated_by")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(content_type=ContentType.objects.get_for_model(ShipLocation))


class ApprovalQueueInlineForCreditLimit(GenericStackedInline):
    verbose_name_plural = "Approval Queues"
    ct_field = "content_type"
    ct_fk_field = "object_id"
    model = ApprovalQueue
    extra = 0
    exclude = ("created_by", "updated_by")
    show_change_link = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(content_type=ContentType.objects.get_for_model(CreditLimit))


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = (
        "party_name",
        "owner_name",
        "witp_code",
        "factory_distance",
        "sales_person",
        "created_at",
        "created_by",
        "status",
        "stage",
    )
    list_filter = (
        "sales_person__username",
        "party_category__name",
        "division",
        "district",
        "transaction_method",
    )
    search_fields = (
        "id",
        "party_name",
        "owner_name",
        "witp_code",
        "bin_number",
        "tin_number",
        "trade_license",
    )

    exclude = ("updated_by",)

    list_per_page = 25
    search_help_text = "search is enabled for {}".format(", ".join(list_filter))

    inlines = (
        DealingInline,
        SecurityChequeInline,
        GuarantorInline,
        ContactPersonsInline,
        AttachmentInline,
        ApprovalQueueInline,
        ExtraAttachmentInline,
    )

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        if not change:
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)


@admin.register(CreditLimit)
class CreditLimitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "party_name",
        "witp_code",
        "created_by",
        "created_at",
        "updated_at",
        "stage",
        "status",
    )
    list_filter = ("status", "stage")
    search_fields = (
        "party_name",
        "witp_code",
    )
    inlines = (
        CreditLimitDetailInline,
        EbsCollectionDetailInline,
        ApprovalQueueInlineForCreditLimit,
    )

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        if not change:
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)


@admin.register(ShipLocation)
class ShipLocationAdmin(admin.ModelAdmin):
    list_display = (
        "party_name",
        "witp_code",
        "receiver_name",
        "receiver_number",
        "marketing_concern",
        "created_by",
        "created_at",
        "updated_at",
        "stage",
        "status",
    )
    list_filter = ("party_name",)
    search_fields = (
        "party_name",
        "witp_code",
        "receiver_name",
        "receiver_number",
    )
    inlines = (ApprovalQueueInlineForShipLocation,)

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        if not change:
            obj.created_by = request.user
        return super().save_model(request, obj, form, change)
