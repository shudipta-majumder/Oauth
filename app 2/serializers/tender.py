from django.db import transaction
from django.db.models import FloatField
from django.db.models.functions import Cast
from rest_framework import serializers

from ..models.participant_bids import ParticipantBid
from ..models.tender import Tender
from ..serializers.contract_agreement import PaymentSerializer, VendorSerializer
from ..serializers.setup_serializers import MinistrySerializer
from ..utils import process_attachment
from .bg_validity_date import BGValidityDateSerializer
from .contract_agreement import ContractAgreementSerializer
from .noa import NoaSerializer
from .participant_bit import ParticipantBidsSerializer
from .product import (
    ProductSerializer,
)
from .time_stamp_serializer import TenderSubmissionTimeStampsSerializer


class TenderSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    bg_valid_dates = BGValidityDateSerializer(many=True, read_only=True)
    tender_submission_timestamp = TenderSubmissionTimeStampsSerializer(
        many=True, read_only=True
    )
    noa = NoaSerializer(read_only=True)
    participant_bid = ParticipantBidsSerializer(many=True, read_only=True)
    contract_agreement = ContractAgreementSerializer(read_only=True)
    ministry = MinistrySerializer(required=False)
    vendor = VendorSerializer(many=True, read_only=True)
    payment = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Tender
        fields = "__all__"

    def to_representation(self, instance):  # noqa: C901
        representation = super().to_representation(instance)
        request = self.context.get("request")

        domain = ""
        if request:
            domain = request.build_absolute_uri("/")
            if domain.endswith("/"):
                domain = domain[:-1]

        representation["bg_attachment"] = process_attachment(
            instance.bg_attachment, domain
        )
        # Process pretender_meeting_attachment
        representation["pretender_meeting_attachment"] = process_attachment(
            instance.pretender_meeting_attachment, domain
        )
        # Process external_application_attach
        representation["external_application_attach"] = process_attachment(
            instance.external_application_attach, domain
        )

        # Process technical_compliance_sheet
        representation["technical_compliance_sheet"] = process_attachment(
            instance.technical_compliance_sheet, domain
        )
        # Process vendor attachments
        if "vendor" in representation:
            vendors = []
            for vendor_data in representation["vendor"]:
                if vendor_data.get("vendor_attachment"):
                    vendor_data["vendor_attachment"] = vendor_data[
                        "vendor_attachment"
                    ].replace(domain, "")
                vendors.append(vendor_data)
            representation["vendor"] = vendors
        # Process payment attachments
        if "payment" in representation:
            payments = []
            for payment_data in representation["payment"]:
                if payment_data.get("payment_attachment"):
                    payment_data["payment_attachment"] = payment_data[
                        "payment_attachment"
                    ].replace(domain, "")
                payments.append(payment_data)
            representation["payment"] = payments

        if instance.participant_bid.exists():
            ordered_bids = instance.participant_bid.annotate(
                bid_price_numeric=Cast("biding_price", FloatField())
            ).order_by("bid_price_numeric")
            representation["participant_bid"] = ParticipantBidsSerializer(
                ordered_bids, many=True
            ).data

        if instance.participant_bid.exists():
            ordered_bids = instance.participant_bid.annotate(
                bid_price_numeric=Cast("biding_price", FloatField())
            ).order_by("bid_price_numeric")
            filtered_bids = ordered_bids.exclude(
                participant_name__name="Walton Digi-Tech Industries Limited"
            )
            lower_bids = filtered_bids[:2]
            representation["lower_bids"] = {
                f"lower_bid_{i+1}": bid.biding_price for i, bid in enumerate(lower_bids)
            }

        if instance.team_name:
            representation["team_name"] = {
                "id": instance.team_name.id,
                "name": instance.team_name.team_name,
            }

        if instance.tender_type:
            representation["tender_type"] = {
                "id": instance.tender_type.id,
                "name": instance.tender_type.type_name,
            }

        return representation


class CustomTenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tender
        fields = "__all__"


class TenderPreSubmissionSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, required=False)
    bg_valid_dates = BGValidityDateSerializer(many=True, required=False)
    tender_submission_timestamp = TenderSubmissionTimeStampsSerializer(
        many=True, required=False
    )
    bg_issue_date = serializers.DateField(allow_null=True, required=False)

    class Meta:
        model = Tender
        fields = "__all__"

    @transaction.atomic
    def update(self, instance, validated_data):
        products_data = validated_data.pop("products", [])
        bg_valid_dates = validated_data.pop("bg_valid_dates", [])
        tender_submission_timestamp_data = validated_data.pop(
            "tender_submission_timestamp", []
        )
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Delete all existing products
        instance.products.all().delete()

        # Create new products
        for product_data in products_data:
            product_data["tender"] = instance.id
            product_serializer = ProductSerializer(data=product_data)
            if product_serializer.is_valid(raise_exception=True):
                product_serializer.save()

        # Update BGValidityDate instances
        instance.bg_valid_dates.all().delete()
        for bg_valid_date in bg_valid_dates:
            bg_valid_date["tender"] = instance.id
            bg_serializer = BGValidityDateSerializer(data=bg_valid_date)
            if bg_serializer.is_valid(raise_exception=True):
                bg_serializer.save()

        instance.tender_submission_timestamp.all().delete()

        for tender_submission_timestamp in tender_submission_timestamp_data:
            tender_submission_timestamp["tender"] = instance.id
            submission_timestamp = TenderSubmissionTimeStampsSerializer(
                data=tender_submission_timestamp
            )
            if submission_timestamp.is_valid(raise_exception=True):
                submission_timestamp.save()

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add both id and name for the ministry field
        if instance.ministry:
            representation["ministry"] = {
                "id": instance.ministry.id,
                "ministry_name": instance.ministry.ministry_name,
            }

        return representation


class TenderPostSubmissionSerializer(serializers.ModelSerializer):
    participant_bid = ParticipantBidsSerializer(many=True, required=False)

    class Meta:
        model = Tender
        fields = [
            "participant_bid",
            "is_tender_submitted",
            "technical_compliance_sheet",
            "result",
            "biding_price_type",
            "biding_price_national",
            "biding_price_international",
            "reason",
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        participant_bids = validated_data.pop("participant_bid", [])

        # Update tender instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update participant bid instance
        instance.participant_bid.all().delete()
        for participant_bid in participant_bids:
            participant_bid.pop("tender", None)
            ParticipantBid.objects.create(tender=instance, **participant_bid)

        return instance


class TenderAnalysisViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tender
        fields = [
            "probable_cost_breakdown_one",
            "probable_cost_breakdown_two",
            "analytics_note",
            "is_bi_analysis_done",
        ]
