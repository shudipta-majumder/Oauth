import uuid
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from pms.models.party_attachment import (  # noqa: F401
        ExtraAttachment,
        PartyAttachment,
    )
    from pms.models.party_dealing import SecurityCheque  # noqa: F401

    from . import Contact  # noqa: F401

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import (
    CASCADE,
    DO_NOTHING,
    BooleanField,
    CharField,
    EmailField,
    FileField,
    ForeignKey,
    IntegerField,
    QuerySet,
    TextChoices,
    UUIDField,
)
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from core.constants import StatusChoices
from dropdown_repository.pms.models import (
    PartyCategoryLov,
    PoliceStationLov,
)
from dropdown_repository.pms.models.repository import (
    BusinessTypeLov,
    DistrictLov,
    DivisionLov,
)
from recommendation_engine.models import (
    ApprovalQueue,
    RecommendationProcess,
    RecommendationSystem,
)

from ..constants import PMSRecommendationStages
from .base import BaseParty

__all__ = ["Party"]


class DistanceTypeChoices(TextChoices):
    D_0_99 = "0_99", _("0-99 KM")
    D_100_199 = "100_199", _("100-199 KM")
    D_200_299 = "200_299", _("200-299 KM")
    D_300_UP = "300_UP", _("300-Above KM")


class Party(BaseParty):
    class TransactionMethodChoices(TextChoices):
        CASH = "cash", _("Cash")
        CREDIT = "credit", _("Credit")
        PARTIAL_PAYMENT = "partial_payment", _("Partial Payment")

    id = UUIDField(editable=False, primary_key=True, default=uuid.uuid4)

    division = ForeignKey(DivisionLov, on_delete=DO_NOTHING, null=True, blank=True)

    district = ForeignKey(DistrictLov, on_delete=DO_NOTHING, null=True, blank=True)

    party_category = ForeignKey(
        PartyCategoryLov,
        on_delete=DO_NOTHING,
        null=True,
        blank=True,
    )

    business_type = ForeignKey(
        BusinessTypeLov, on_delete=DO_NOTHING, null=True, blank=True
    )

    email = EmailField(null=True, blank=True)

    police_station = ForeignKey(
        PoliceStationLov,
        on_delete=DO_NOTHING,
        null=True,
        blank=True,
    )

    factory_distance = CharField(
        max_length=255,
        verbose_name=_("Factory Distance (Km)"),
        choices=DistanceTypeChoices.choices,
        default=DistanceTypeChoices.D_0_99,
    )

    transaction_method = CharField(
        verbose_name=_("Transaction Method"),
        max_length=99,
        choices=TransactionMethodChoices.choices,
        default=TransactionMethodChoices.CASH,
    )

    party_present_addr = CharField(
        verbose_name="Party Present Address",
        null=True,
        blank=True,
        max_length=255,
        default=None,
    )

    stepper_index = IntegerField(default=0)

    sales_person = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE)

    stage = CharField(
        max_length=255,
        choices=PMSRecommendationStages.choices,
        default=None,
        null=True,
        blank=True,
    )

    status = CharField(
        max_length=255,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )

    system = ForeignKey(RecommendationSystem, on_delete=DO_NOTHING)
    process = ForeignKey(RecommendationProcess, on_delete=DO_NOTHING)
    approval_queues = GenericRelation(ApprovalQueue)

    trade_license = CharField(
        verbose_name="Trade License", max_length=255, null=True, blank=True
    )
    trade_license_file = FileField(
        upload_to="attachments/party",
        null=True,
        blank=True,
        verbose_name="Trade License File",
    )
    bin_number = CharField(
        verbose_name="VAT/BIN Number", max_length=255, null=True, blank=True
    )
    bin_number_file = FileField(
        upload_to="attachments/party",
        null=True,
        blank=True,
        verbose_name="Business Identification Numbers",
    )
    tin_number = CharField(
        verbose_name="TIN Number", max_length=255, null=True, blank=True
    )
    tin_number_file = FileField(
        upload_to="attachments/party",
        null=True,
        blank=True,
        verbose_name="Taxpayer Identification Numbers",
    )

    ugc_certificate_no = CharField(
        "UGC Certificate No", max_length=255, null=True, blank=True
    )

    ugc_certificate_file = FileField(
        upload_to="attachments/party",
        null=True,
        blank=True,
        verbose_name="UGC Certificate File",
    )

    remarks = CharField(null=True, blank=True, max_length=500)

    next_node: "Party" = ForeignKey(
        "self", on_delete=CASCADE, related_name="rev_nodes", null=True, blank=True
    )
    history_current_step = IntegerField(
        null=True, blank=True, verbose_name="History Current Step"
    )
    history_current_stage = CharField(
        null=True, blank=True, verbose_name="History Current Stage", max_length=88
    )

    is_tenderable = BooleanField(default=False, verbose_name="Party is Tenderable ?")
    is_ebs_imported_party = BooleanField(
        default=False, verbose_name="Is imported From Oracle DB ?"
    )

    contacts = QuerySet["Contact"]
    attachments = QuerySet["PartyAttachment"]
    extras = QuerySet["ExtraAttachment"]
    rev_nodes = QuerySet["Party"]
    security_cheques = QuerySet["SecurityCheque"]

    def _validate_fk_dealing(self, required_fields_arr: List[str]):
        if not self.dealing.mou or not self.dealing.mou_file:
            required_fields_arr.append("")

    def _validate_fk_contacts(self, required_fields_arr: List[str]):
        for contact in self.contacts.all():
            if not contact.phone:
                required_fields_arr.append("")

    def _validate_fk_party_authorization_letter(self, required_fields_arr: List[str]):
        for attach in self.attachments.all():
            if not attach.party_authorization_letter.name:
                required_fields_arr.append("")

    def _validate_fk_party_credit_rating_certificate(
        self, required_fields_arr: List[str]
    ):
        for attach in self.attachments.all():
            if not attach.credit_rating_certificate.name:
                required_fields_arr.append("")

    def _get_required_fields(self) -> List[str]:  # noqa: C901
        general_corporate_category = PartyCategoryLov.objects.get(codename="10001")
        government_category = PartyCategoryLov.objects.get(codename="20001")
        pcb_category = PartyCategoryLov.objects.get(codename="30001")
        education_category = PartyCategoryLov.objects.get(codename="40001")
        finance_category = PartyCategoryLov.objects.get(codename="50001")

        required_fields = []

        def _get_common_required_fields():
            return [
                "trade_license_file",
                "bin_number_file",
                "tin_number_file",
                "trade_license",
                "bin_number",
                "tin_number",
            ]

        if self.party_category == general_corporate_category:
            required_fields = _get_common_required_fields()
            self._validate_fk_dealing(required_fields)
            self._validate_fk_contacts(required_fields)
            self._validate_fk_party_authorization_letter(required_fields)
        elif self.party_category == education_category:
            required_fields = [
                "tin_number_file",
                "bin_number_file",
                "tin_number",
                "bin_number",
            ]
            self._validate_fk_contacts(required_fields)
            self._validate_fk_party_authorization_letter(required_fields)
        elif self.party_category == finance_category:
            required_fields = _get_common_required_fields()
            self._validate_fk_dealing(required_fields)
            self._validate_fk_contacts(required_fields)
            self._validate_fk_party_authorization_letter(required_fields)
            self._validate_fk_party_credit_rating_certificate(required_fields)
        elif self.party_category == pcb_category:
            required_fields = _get_common_required_fields()
            self._validate_fk_dealing(required_fields)
            self._validate_fk_contacts(required_fields)
            self._validate_fk_party_authorization_letter(required_fields)
        elif self.party_category == government_category:
            self._validate_fk_dealing(required_fields)
            self._validate_fk_contacts(required_fields)
        else:
            pass

        return required_fields

    def has_all_required_docs(self, required_fields=None):
        """
        Checks if all required document fields are provided.

        :param required_fields: List of field names to check.
        :return: Boolean indicating if all required fields are present.
        """
        if required_fields is None:
            required_fields = self._get_required_fields()

        for field_name in required_fields:
            value = getattr(self, field_name, None)

            # Check if the field is a FileField or a regular field
            if isinstance(value, FieldFile):
                if not value.name:  # Check if the file is uploaded
                    return False
            elif value in [None, "", []]:  # Handle empty values for normal fields
                return False

        return True

    def __str__(self) -> str:
        return f"{self.party_name} - {self.owner_name}"

    class Meta:
        db_table = "pms_party"
        verbose_name = "Party"
        verbose_name_plural = "🏫 Parties"
