from rest_framework.serializers import ModelSerializer

from dropdown_repository.pms.serializers import (
    BankIssuerSerializer,
)

from ..models import Guarantee, PartyDealing, SecurityCheque

__all__ = ["DealingSerializer", "SecurityChequeSerializer", "GuaranteeSerializer"]


class DealingSerializer(ModelSerializer):
    class Meta:
        model = PartyDealing
        fields = "__all__"


class SecurityChequeSerializer(ModelSerializer):
    def to_representation(self, instance: SecurityCheque):
        response = super().to_representation(instance)
        request = self.context.get("request")

        issuer_bank_instance = BankIssuerSerializer(instance=instance.issuer_bank)
        issuer_branch_instance = BankIssuerSerializer(instance=instance.issuer_branch)

        response["issuer_bank"] = issuer_bank_instance.data
        response["issuer_branch"] = issuer_branch_instance.data

        if request:
            # Get the URI for the attachment field without the domain
            if instance.cheque_file:
                cheque_url = instance.cheque_file.url
                domain = request.build_absolute_uri("/")[:-1]
                response["cheque_file"] = cheque_url.replace(domain, "")

        return response

    class Meta:
        model = SecurityCheque
        fields = "__all__"


class GuaranteeSerializer(ModelSerializer):
    def to_representation(self, instance: SecurityCheque):
        response = super().to_representation(instance)
        request = self.context.get("request")

        issuer_bank_instance = BankIssuerSerializer(instance=instance.issuer_bank)
        issuer_branch_instance = BankIssuerSerializer(instance=instance.issuer_branch)

        response["issuer_bank"] = issuer_bank_instance.data
        response["issuer_branch"] = issuer_branch_instance.data

        if request:
            # Get the URI for the attachment field without the domain
            if instance.attachment:
                cheque_url = instance.attachment.url
                domain = request.build_absolute_uri("/")[:-1]
                response["attachment"] = cheque_url.replace(domain, "")

        return response

    class Meta:
        model = Guarantee
        fields = "__all__"
