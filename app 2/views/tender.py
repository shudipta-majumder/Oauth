from logging import getLogger

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response

from core.openapi_metadata.metadata import OpenApiTags
from core.pagination import StandardResultSetPagination
from core.permissions import UserAccessControl
from core.renderer import CustomRenderer

from ..models.tender import Participant, Tender
from ..serializers.tender import (
    TenderAnalysisViewSerializer,
    TenderPostSubmissionSerializer,
    TenderPreSubmissionSerializer,
    TenderSerializer,
)
from ..utils import parse_json_data


@extend_schema(tags=[OpenApiTags.TMS_TENDER])
class TenderListCreateView(ListCreateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    serializer_class = TenderSerializer
    renderer_classes = [
        CustomRenderer,
    ]
    pagination_class = StandardResultSetPagination

    def get_queryset(self):
        queryset = Tender.objects.all().order_by("-created_at")
        return queryset

    def get(self, request, *args, **kwargs):
        id = self.kwargs.get("id", None)
        self.pagination_class.page_size = 10
        if id is not None:
            try:
                tender = Tender.objects.get(id=id)
                serializer = self.get_serializer(tender)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Tender.DoesNotExist:
                raise NotFound(detail="Tender not found.")  # noqa: B904
        else:
            return super().get(request, *args, **kwargs)


@extend_schema(tags=[OpenApiTags.TMS_TENDER])
class TenderUpdateView(generics.UpdateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    queryset = Tender.objects.all()
    serializer_class = TenderPreSubmissionSerializer
    lookup_field = "id"
    renderer_classes = [
        CustomRenderer,
    ]

    def get_queryset(self):
        id = self.kwargs.get("id")
        return Tender.objects.filter(id=id)

    def perform_update(self, serializer):  # noqa: C901
        products_data = parse_json_data(
            self.request.data.get("products", "[]"), "Products data"
        )
        bg_valid_dates = parse_json_data(
            self.request.data.get("bg_valid_dates", "[]"), "BG Validity Date data"
        )
        tender_submission_timestamp = parse_json_data(
            self.request.data.get("tender_submission_timestamp", "[]"),
            "Tender Submission Timestamp data",
        )
        # Validate and map the product fields
        mapped_products_data = []
        for product in products_data:
            tender_uuid = product.get("tender")
            tender_instance = get_object_or_404(Tender, id=tender_uuid)
            mapped_product = {
                "product_name": product.get("productName"),
                "product_brand": product.get("productBrand"),
                "model_number": product.get("modelNumber"),
                "warranty": product.get("warranty"),
                "product_qty": product.get("productQty"),
                "tender": tender_instance,
            }
            mapped_products_data.append(mapped_product)

        # Retrieve Tender instance for each BG Extended Date
        mapped_bg_valid_date = []
        for bg_date in bg_valid_dates:
            tender_uuid = bg_date.get("tender")
            tender_instance = get_object_or_404(Tender, id=tender_uuid)
            mapped_bg_date = {
                "bg_valid_date": bg_date.get("bgValidDate"),
                "tender": tender_instance,
            }
            mapped_bg_valid_date.append(mapped_bg_date)

        # Retrieve Tender instance for each Tender Submission Timestamp
        mapped_tender_submission_timestamp = []
        for submission_timestamp in tender_submission_timestamp:
            tender_uuid = submission_timestamp.get("tender")
            tender_instance = get_object_or_404(Tender, id=tender_uuid)
            mapped_timestamp = {
                "submission_date": submission_timestamp.get("submissionDate"),
                # "submission_time": submission_timestamp.get("submissionTime"),
                "tender": tender_instance,
            }
            mapped_tender_submission_timestamp.append(mapped_timestamp)

        # Save updated data
        serializer.save(
            products=mapped_products_data,
            bg_valid_dates=mapped_bg_valid_date,
            tender_submission_timestamp=mapped_tender_submission_timestamp,
        )


@extend_schema(tags=[OpenApiTags.TMS_TENDER])
class TenderPostSubmission(generics.UpdateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    pagination_class = []
    renderer_classes = [
        CustomRenderer,
    ]
    serializer_class = TenderPostSubmissionSerializer
    queryset = Tender.objects.all()
    lookup_field = "id"

    def get_queryset(self):
        id = self.kwargs.get("id")
        tender = Tender.objects.filter(id=id)
        return tender

    def perform_update(self, serializer):
        participant_bids = parse_json_data(
            self.request.data.get("participant_bid", "[]"), "Participant Bid"
        )

        mapped_participants_data = []
        for participant_bid in participant_bids:
            tender_uuid = participant_bid.get("tender")
            participant_id = participant_bid.get("participantId")
            participant_instance = get_object_or_404(Participant, id=participant_id)
            tender_instance = get_object_or_404(Tender, id=tender_uuid)
            mapped_participant = {
                "participant_name": participant_instance,
                "biding_price": participant_bid.get("bidingPrice"),
                "tender": tender_instance,
            }
            mapped_participants_data.append(mapped_participant)

        serializer.save(participant_bid=mapped_participants_data)


@extend_schema(tags=[OpenApiTags.TENDER_ANALYSIS])
class TenderAnalysisView(generics.UpdateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    renderer_classes = [CustomRenderer]
    serializer_class = TenderAnalysisViewSerializer
    queryset = Tender.objects.all()
    lookup_field = "id"

    def perform_update(self, serializer):
        # Set is_bi_analysis_done to True
        serializer.save(is_bi_analysis_done=True)


@extend_schema(tags=[OpenApiTags.TMS_TENDER])
class CompleteTenderListView(generics.ListAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    renderer_classes = [CustomRenderer]
    queryset = Tender.objects.filter(is_open=False).order_by("-updated_at")
    serializer_class = TenderSerializer
    filter_backends = [SearchFilter]
    search_fields = [
        "tender_id",
        "team_name__team_name",
        "kam_name",
        "procuring_entity",
    ]
    pagination_class = StandardResultSetPagination

    def get(self, request, *args, **kwargs):
        self.pagination_class.page_size = 10
        return super().get(request, *args, **kwargs)


@extend_schema(tags=[OpenApiTags.TMS_TENDER])
class OnGoingTenderListView(generics.ListAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    renderer_classes = [CustomRenderer]
    queryset = Tender.objects.filter(is_open=True).order_by("-updated_at")
    serializer_class = TenderSerializer
    filter_backends = [SearchFilter]
    search_fields = [
        "tender_id",
        "team_name__team_name",
        "kam_name",
        "procuring_entity",
    ]
    pagination_class = StandardResultSetPagination

    def get(self, request, *args, **kwargs):
        self.pagination_class.page_size = 10
        return super().get(request, *args, **kwargs)
