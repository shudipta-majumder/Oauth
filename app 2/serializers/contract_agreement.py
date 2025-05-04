from django.db import transaction
from rest_framework import serializers

from ..models.contract_agreement import (
    ContractAgreement,
    Payment,
    PGReleasedDate,
    Vendor,
)
from ..utils import process_attachment


class PGReleasedDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PGReleasedDate
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        domain = ""
        if request:
            domain = request.build_absolute_uri("/")
            if domain.endswith("/"):
                domain = domain[:-1]

        representation["payment_attachment"] = process_attachment(
            instance.payment_attachment, domain
        )

        return representation


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        domain = ""
        if request:
            domain = request.build_absolute_uri("/")
            if domain.endswith("/"):
                domain = domain[:-1]

        representation["vendor_attachment"] = process_attachment(
            instance.vendor_attachment, domain
        )
        return representation


class ContractAgreementSerializer(serializers.ModelSerializer):
    pg_released_date = PGReleasedDateSerializer(many=True, required=False)

    class Meta:
        model = ContractAgreement
        fields = "__all__"

    @transaction.atomic
    def create(self, validated_data):
        pg_released_dates = validated_data.pop("pg_released_date", [])
        tender = validated_data.get("tender")
        # Create the NotificationOfAward instance
        contract_instance = ContractAgreement.objects.create(**validated_data)

        # Create associated BGReleasedDate instances
        for pg_released_date in pg_released_dates:
            tender = pg_released_date.pop("tender")
            PGReleasedDate.objects.create(tender=tender, **pg_released_date)

        return contract_instance

    @transaction.atomic
    def update(self, instance, validated_data):
        pg_released_dates = validated_data.pop("pg_released_date", [])
        tender = instance.tender
        PGReleasedDate.objects.filter(tender=tender).delete()
        for pg_released_date in pg_released_dates:
            tender = pg_released_date.pop("tender")
            PGReleasedDate.objects.create(tender=tender, **pg_released_date)
        instance = super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        domain = ""
        if request:
            domain = request.build_absolute_uri("/")
            if domain.endswith("/"):
                domain = domain[:-1]

        representation["contract_agreement_attch"] = process_attachment(
            instance.contract_agreement_attch, domain
        )

        representation["completion_certificate"] = process_attachment(
            instance.completion_certificate, domain
        )
        representation["pg_released_date"] = PGReleasedDateSerializer(
            instance.tender.pg_released_date.all(), many=True
        ).data

        return representation
