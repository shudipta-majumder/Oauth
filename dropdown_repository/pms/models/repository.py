from django.db import models

from core.mixins import AuditLogMixin

__all__ = [
    "DivisionLov",
    "DistrictLov",
    "BusinessZoneLov",
    "PartyCategoryLov",
    "PoliceStationLov",
    "BankIssuerLov",
    "BranchIssuerBankLov",
    "BusinessTypeLov",
]


class DivisionLov(AuditLogMixin):
    name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    bn_name = models.CharField(max_length=255, unique=True, null=True, blank=True)
    lat = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=4)
    long = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=4)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = "Divisions"
        verbose_name = "Division"


class DistrictLov(AuditLogMixin):
    name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    is_active = models.BooleanField(default=True)
    division = models.ForeignKey(
        DivisionLov, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = "Districts"
        verbose_name = "District"


# Create your models here.
class BusinessZoneLov(AuditLogMixin):
    division = models.ForeignKey(DivisionLov, on_delete=models.DO_NOTHING)
    district = models.ForeignKey(DistrictLov, on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return f"{self.division} | {self.district}"

    class Meta:
        db_table = "pms_lov_business_zone"
        verbose_name = "Business Zone"
        verbose_name_plural = "Business Zones"


class BusinessTypeLov(AuditLogMixin):
    name = models.CharField(
        verbose_name="Name",
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        db_index=True,
    )
    is_active = models.BooleanField(verbose_name="Active Status", default=True)

    business_types = models.QuerySet["PartyCategoryLov"]

    class Meta:
        db_table = "pms_lov_business_type_lov"
        verbose_name = "Business Type"
        verbose_name_plural = "Business Types"

    def __str__(self) -> str:
        return self.name


class PartyCategoryLov(AuditLogMixin):
    business_type = models.ForeignKey(
        BusinessTypeLov,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="business_types",
    )
    name = models.CharField(
        verbose_name="Party Category",
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        db_index=True,
    )
    codename = models.CharField(
        verbose_name="Code Name",
        max_length=255,
        null=False,
        blank=False,
        default="NA",
    )
    is_active = models.BooleanField(verbose_name="Active Status", default=True)

    class Meta:
        db_table = "pms_lov_party_category"
        verbose_name = "Party Category"
        verbose_name_plural = "Party Categories"

    def __str__(self) -> str:
        return self.name


class PoliceStationLov(AuditLogMixin):
    name = models.CharField(
        verbose_name="Police Station",
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        db_index=True,
    )
    phone = models.CharField(max_length=18, null=True, blank=True)
    is_active = models.BooleanField(verbose_name="Active Status", default=True)
    division = models.ForeignKey(
        DivisionLov, on_delete=models.CASCADE, null=True, blank=True
    )
    district = models.ForeignKey(
        DistrictLov, on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        db_table = "pms_lov_police_station"
        verbose_name = "Police Station"
        verbose_name_plural = "Police Stations"

    def __str__(self) -> str:
        return self.name


class BankIssuerLov(AuditLogMixin):
    name = models.CharField(
        max_length=255, unique=True, db_index=True, verbose_name="Bank Name"
    )
    is_active = models.BooleanField(verbose_name="Active Status", default=True)

    class Meta:
        db_table = "pms_lov_bank"
        verbose_name = "Bank"
        verbose_name_plural = "Banks"

    def __str__(self) -> str:
        return self.name


class BranchIssuerBankLov(AuditLogMixin):
    name = models.CharField(
        verbose_name="Branch Name", unique=True, db_index=True, max_length=255
    )
    is_active = models.BooleanField(verbose_name="Active Status", default=True)
    bank = models.ForeignKey(BankIssuerLov, on_delete=models.CASCADE)

    class Meta:
        db_table = "pms_lov_branch"
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self) -> str:
        return self.name
