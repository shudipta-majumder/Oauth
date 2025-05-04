from django.contrib import admin

from .models.contract_agreement import (
    ContractAgreement,
    Payment,
    PGReleasedDate,
    Vendor,
)
from .models.noa import BGReleasedDate, NotificationOfAward
from .models.notification import Notification
from .models.participant_bids import ParticipantBid
from .models.product import Product, ProductAnalysis, ProductSpacification
from .models.tender import (
    BGValidityDate,
    Ministry,
    Participant,
    Team,
    Tender,
    TenderSubmissionTimeStamps,
    TenderType,
)


# Inlines for related models in the Tender admin interface
class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = (
        "product_name",
        "product_brand",
        "model_number",
        "warranty",
        "product_qty",
        "is_reviewed",
    )
    can_delete = True


class BGValidityDateInline(admin.TabularInline):
    model = BGValidityDate
    extra = 0
    fields = ("bg_valid_date", "tender")
    can_delete = True


class TenderSubmissionTimeStampsInline(admin.TabularInline):
    model = TenderSubmissionTimeStamps
    extra = 0
    fields = ("submission_date",)
    can_delete = True


class ParticipantBidsInline(admin.TabularInline):
    model = ParticipantBid
    extra = 0
    fields = ("participant_name", "biding_price", "tender")
    can_delete = True


class NotificationOfAwardInline(admin.TabularInline):
    model = NotificationOfAward
    extra = 0
    fields = (
        "noa_status",
        "noa_receiving_date",
        "noa_acceptance_deadline",
        "contract_agreement_deadline",
        "pg_amount",
        "pg_issue_date",
        "pg_validity_date",
        "tender",
    )
    can_delete = True


class ContractAgreementInline(admin.TabularInline):
    model = ContractAgreement
    extra = 0
    fields = (
        "contract_agreement_attch",
        "contract_agreement_date",
        "delivery_deadline_input_days",
        "delivery_deadline",
        "delivery_start_date",
        "delivery_complition_date",
        "is_tender_complete",
    )
    can_delete = True


class VendorInline(admin.TabularInline):
    model = Vendor
    extra = 0
    fields = ("vendor_name", "tender")
    can_delete = True


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("payment_amount", "tender")
    can_delete = True


# Admin configurations for all models.
class MinistryAdmin(admin.ModelAdmin):
    list_display = ("ministry_name",)


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "product_brand",
        "model_number",
        "warranty",
        "product_qty",
        "tender",
        "is_reviewed",
    )


class TeamAdmin(admin.ModelAdmin):
    list_display = ("team_name",)


class TenderAdmin(admin.ModelAdmin):
    list_display = (
        "tender_id",
        "team_name",
        "kam_name",
        "tender_type",
        # "tender_description",
        "procuring_entity",
        "is_open",
        "ministry",
        "bg_amount",
        "bg_issue_date",
    )
    search_fields = ("tender_id",)
    list_filter = ("is_open",)
    ordering = ("-created_at",)
    inlines = [
        ProductInline,
        BGValidityDateInline,
        TenderSubmissionTimeStampsInline,
        ParticipantBidsInline,
        NotificationOfAwardInline,
        ContractAgreementInline,
        VendorInline,
        PaymentInline,
    ]


class TenderTypeAdmin(admin.ModelAdmin):
    list_display = ("type_name",)


class BGValidityDateAdmin(admin.ModelAdmin):
    list_display = ("bg_valid_date", "tender")


class TenderSubmissionTimeStampsAdmin(admin.ModelAdmin):
    list_display = ("submission_date",)


class ParticipantsAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


class ParticipantBidsAdmin(admin.ModelAdmin):
    list_display = ("participant_name", "biding_price", "tender")


class NotificationOfAwardAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "noa_status",
        "noa_receiving_date",
        "noa_acceptance_deadline",
        "contract_agreement_deadline",
        "pg_amount",
        "pg_issue_date",
        "pg_validity_date",
        "tender",
    )
    search_fields = ("id", "tender__id", "tender__tender_id")
    list_filter = ("noa_status",)

    def __str__(self):
        return str(self.id)


@admin.register(ContractAgreement)
class ContractAgreementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "contract_agreement_date",
        "delivery_deadline",
        "delivery_start_date",
        "delivery_complition_date",
        "is_tender_complete",
    )
    search_fields = ("id", "tender__id", "tender__tender_id")
    list_filter = ("is_tender_complete",)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("id", "vendor_name", "tender")
    search_fields = ("vendor_name",)
    list_filter = ("tender",)
    ordering = ("vendor_name",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "payment_amount", "tender")
    search_fields = ("id", "tender")
    list_filter = ("tender",)
    ordering = ("-payment_amount",)


# @admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "tender",
        "notification_type",
        "team_name",
        "tender_type",
        "deadline",
        "remaining_time",
        "procurring_entity",
        "kam_name",
    )
    search_fields = ("id", "tender")
    list_filter = ("tender__tender_id",)


class ProductSpacificationAdmin(admin.ModelAdmin):
    list_display = (
        "spacification_name",
        "required_spacification",
        "walton_spacification",
        "compettitors_spacification_one",
        "compettitors_spacification_two",
        "product",
    )


class ProductAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "walton_price",
        "lower_one_breakdown",
        "lower_two_breakdown",
        "product",
    )


class BGReleasedDateAdmin(admin.ModelAdmin):
    list_display = ("date", "is_bg_released", "tender")


class PGReleasedDateAdmin(admin.ModelAdmin):
    list_display = ("date", "is_pg_released", "tender")
    list_filter = ("is_pg_released", "date")
    search_fields = ("tender__tender_id", "is_pg_released")


admin.site.register(PGReleasedDate, PGReleasedDateAdmin)
admin.site.register(BGReleasedDate, BGReleasedDateAdmin)
admin.site.register(ProductAnalysis, ProductAnalysisAdmin)
admin.site.register(ProductSpacification, ProductSpacificationAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationOfAward, NotificationOfAwardAdmin)
admin.site.register(ParticipantBid, ParticipantBidsAdmin)
admin.site.register(Participant, ParticipantsAdmin)
admin.site.register(TenderSubmissionTimeStamps, TenderSubmissionTimeStampsAdmin)
admin.site.register(Tender, TenderAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Ministry, MinistryAdmin)
admin.site.register(TenderType, TenderTypeAdmin)
admin.site.register(BGValidityDate, BGValidityDateAdmin)
