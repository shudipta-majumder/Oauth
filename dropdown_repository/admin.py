from django.contrib import admin

from .pms.models import (
    BankIssuerLov,
    BranchIssuerBankLov,
    BusinessZoneLov,
    DistrictLov,
    DivisionLov,
    PartyCategoryLov,
    PoliceStationLov,
)


class DistrictLovInline(admin.TabularInline):
    fields = ("name", "is_active")
    model = DistrictLov
    extra = 0


@admin.register(DivisionLov)
class DivisionLovAdmin(admin.ModelAdmin):
    list_display = ("name", "bn_name", "lat", "long", "is_active")
    fields = ("name", "bn_name", "lat", "long", "is_active")

    inlines = (DistrictLovInline,)


class BranchInlineSet(admin.TabularInline):
    model = BranchIssuerBankLov
    extra = 0
    fields = (
        "name",
        "is_active",
    )


@admin.register(BusinessZoneLov)
class BusinessZoneAdmin(admin.ModelAdmin):
    list_display = (
        "division",
        "district",
    )
    fields = (
        "division",
        "district",
    )


@admin.register(BankIssuerLov)
class BankIssuerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
    )
    fields = (
        "name",
        "is_active",
    )
    inlines = (BranchInlineSet,)


@admin.register(PartyCategoryLov)
class PartyCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "codename",
        "name",
        "is_active",
    )
    fields = (
        "name",
        "codename",
        "is_active",
    )


@admin.register(PoliceStationLov)
class PoliceStationAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "division", "is_active")
    fields = ("name", "phone", "division", "district", "is_active")
    list_filter = ("division", "is_active")
    search_fields = ("name", "division")
