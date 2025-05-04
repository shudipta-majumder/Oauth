import uuid

from django.db.models import (
    CASCADE,
    DO_NOTHING,
    CharField,
    DateField,
    FileField,
    FloatField,
    ForeignKey,
    Model,
    OneToOneField,
    UUIDField,
)
from django.utils.translation import gettext_lazy as _

from dropdown_repository.pms.models import (
    BankIssuerLov,
    BranchIssuerBankLov,
)

from . import Party

__all__ = ["PartyDealing", "SecurityCheque", "Guarantee"]


class PartyDealing(Model):
    id = UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    mou = CharField(verbose_name="MOU/PO/NOA/RFQ", max_length=99, null=True, blank=True)

    mou_file = FileField(
        upload_to="attachments/party_dealing",
        null=True,
        blank=True,
        verbose_name="MOU/RFQ/NOA/PO/WO File",
    )
    remarks = CharField(
        verbose_name=_("Remarks"), max_length=255, null=True, blank=True
    )
    party = OneToOneField(
        Party, on_delete=CASCADE, null=False, blank=False, related_name="dealing"
    )

    def __str__(self) -> str:
        return f"{self.id} - {self.party.party_name} - {self.party.owner_name}"

    class Meta:
        db_table = "pms_dealing_information"
        verbose_name = "Party Dealing"
        verbose_name_plural = "📜 Party Dealings"


class SecurityCheque(Model):
    cheque_number = CharField(
        verbose_name=("Security Check / BG Number"),
        max_length=99,
        null=True,
        blank=True,
        default=None,
    )
    cheque_amount = FloatField(verbose_name=_("Security cheque Amount"), default=0)
    cheque_file = FileField(
        upload_to="attachments/party_dealing",
        null=True,
        blank=True,
        default=None,
        verbose_name="Security Cheque Image",
    )
    cheque_issue_date = DateField(
        verbose_name=_("Issue Date"),
        null=True,
        blank=True,
        default=None,
    )
    cheque_maturity_date = DateField(
        verbose_name=_("Maturity Date"),
        null=True,
        blank=True,
        default=None,
    )
    issuer_bank = ForeignKey(
        BankIssuerLov,
        on_delete=DO_NOTHING,
        verbose_name=_("Bank Name"),
        null=True,
        blank=True,
        default=None,
    )
    issuer_branch = ForeignKey(
        BranchIssuerBankLov,
        on_delete=DO_NOTHING,
        verbose_name=_("Branch Name"),
        null=True,
        blank=True,
        default=None,
    )
    party = ForeignKey(Party, on_delete=CASCADE, related_name="security_cheques")
    account_of = CharField(
        verbose_name=_("Account Of"), max_length=99, null=True, blank=True, default=None
    )

    def __str__(self) -> str:
        return f"{self.id} - {self.cheque_number} - {self.cheque_amount}"

    class Meta:
        db_table = "pms_security_cheque"
        verbose_name = "Security Cheque"
        verbose_name_plural = "📜 Security Cheque"


class Guarantee(Model):
    identifier = CharField(
        verbose_name=("BG/PG Number"),
        max_length=99,
        null=True,
        blank=True,
        default=None,
    )
    amount = FloatField(verbose_name=_("Amount"), default=0)
    attachment = FileField(
        upload_to="attachments/gurantee_collections",
        null=True,
        blank=True,
        default=None,
        verbose_name="Security Cheque Image",
    )
    issue_date = DateField(
        verbose_name=_("Issue Date"),
        null=True,
        blank=True,
        default=None,
    )
    expiry_date = DateField(
        verbose_name=_("Expiry Date"),
        null=True,
        blank=True,
        default=None,
    )
    issuer_bank = ForeignKey(
        BankIssuerLov,
        on_delete=DO_NOTHING,
        verbose_name=_("Bank Name"),
        null=True,
        blank=True,
        default=None,
    )
    issuer_branch = ForeignKey(
        BranchIssuerBankLov,
        on_delete=DO_NOTHING,
        verbose_name=_("Branch Name"),
        null=True,
        blank=True,
        default=None,
    )
    party = ForeignKey(Party, on_delete=CASCADE, related_name="guarantee_collections")
    account_of = CharField(
        verbose_name=_("Account Of"), max_length=99, null=True, blank=True, default=None
    )

    def __str__(self) -> str:
        return f"{self.id} - {self.amount} - {self.identifier}"

    class Meta:
        db_table = "pms_guarantee_store"
        verbose_name = "Guarantee"
        verbose_name_plural = "📜 Guarantee Collections"
