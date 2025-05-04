from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework.generics import CreateAPIView, DestroyAPIView, UpdateAPIView

from core.openapi_metadata.metadata import OpenApiTags
from core.permissions import UserAccessControl
from core.renderer import CustomRenderer

from ..models.contract_agreement import ContractAgreement, Payment, Vendor
from ..models.tender import Tender
from ..serializers.contract_agreement import (
    ContractAgreementSerializer,
    PaymentSerializer,
    VendorSerializer,
)
from ..utils import parse_json_data


@extend_schema(tags=[OpenApiTags.CONTRACT_AGREEMENT])
class ContractAgreementCreateView(CreateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    queryset = ContractAgreement.objects.all()
    serializer_class = ContractAgreementSerializer
    renderer_classes = [CustomRenderer]

    def perform_create(self, serializer):
        pg_released_dates = parse_json_data(
            self.request.data.get("pg_released_date", "[]"), "PG Release date."
        )
        mapped_pg_date = []
        for pg_date in pg_released_dates:
            tender_uuid = pg_date.get("tender")
            tender_instance = get_object_or_404(Tender, id=tender_uuid)
            mapped_date = {
                "date": pg_date.get("date"),
                "is_pg_released": pg_date.get("isPgReleased"),
                "tender": tender_instance,
            }
            mapped_pg_date.append(mapped_date)
        serializer.save(pg_released_date=mapped_pg_date)


@extend_schema(tags=[OpenApiTags.CONTRACT_AGREEMENT])
class ContractAgreementUpdateView(UpdateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    queryset = ContractAgreement.objects.all()
    serializer_class = ContractAgreementSerializer
    renderer_classes = [CustomRenderer]
    lookup_field = "id"

    def perform_update(self, serializer):
        pg_released_dates = parse_json_data(
            self.request.data.get("pg_released_date", "[]"), "PG Release date."
        )
        mapped_pg_date = []
        for pg_date in pg_released_dates:
            tender_uuid = pg_date.get("tender")
            tender_instance = get_object_or_404(Tender, id=tender_uuid)
            mapped_date = {
                "date": pg_date.get("date"),
                "is_pg_released": pg_date.get("isPgReleased"),
                "tender": tender_instance,
            }
            mapped_pg_date.append(mapped_date)
        serializer.save(pg_released_date=mapped_pg_date)


@extend_schema(tags=[OpenApiTags.VENDOR])
class VendorCreateView(CreateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    serializer_class = VendorSerializer
    queryset = Vendor.objects.all()
    renderer_classes = [CustomRenderer]


@extend_schema(tags=[OpenApiTags.VENDOR])
class VendorUpdateAPIView(UpdateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    serializer_class = VendorSerializer
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    lookup_field = "id"


@extend_schema(tags=[OpenApiTags.VENDOR])
class VendorDeleteAPIView(DestroyAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    serializer_class = VendorSerializer
    queryset = Vendor.objects.all()
    lookup_field = "id"


@extend_schema(tags=[OpenApiTags.PAYMENT])
class PaymentCreateView(CreateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    renderer_classes = [CustomRenderer]


@extend_schema(tags=[OpenApiTags.PAYMENT])
class PaymentUpdateAPIView(UpdateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    serializer_class = PaymentSerializer
    lookup_field = "id"

    def get_queryset(self):
        id = self.kwargs.get("id")
        payment = Payment.objects.filter(id=id)
        return payment


@extend_schema(tags=[OpenApiTags.PAYMENT])
class PaymentDeleteAPIView(DestroyAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    lookup_field = "id"
