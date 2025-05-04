import uuid
from datetime import datetime, timedelta
from http import HTTPMethod
from logging import getLogger

from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from rest_framework import exceptions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from core.constants import StatusChoices
from core.openapi_metadata.metadata import OpenApiTags
from core.pagination import StandardResultSetPagination
from core.renderer import CustomRenderer
from pms.constants import PMSRecommendationStages

from ..models import ShipLocation
from ..serializers import ShipLocationCreateSerializer, ShipLocationSerializer
from ..services.ship_location_services import ShipLocationService
from .ebs_party import fetch_basic_party

logger = getLogger("pms.views.ship_location")

__all__ = ["ShipLocationViewSet"]


def is_incharge(role: Group) -> bool:
    if not role:
        return False
    return role.name.lower() == PMSRecommendationStages.INCHARGE.value.lower()


class ShipLocationApplicationNotFoundException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Application does not exists.")
    default_code = "not_found"


class PartyNotFoundException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Party does not exists.")
    default_code = "party_error"


@extend_schema(tags=[OpenApiTags.PMS_SHIP_LOCATION_APPLICATION])
class ShipLocationViewSet(ViewSet):
    queryset = ShipLocation.objects.all().order_by("-created_at")
    serializer_class = ShipLocationSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    pagination_class = StandardResultSetPagination
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "q",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                "status",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                enum=StatusChoices,
            ),
            OpenApiParameter(
                "stage",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                enum=PMSRecommendationStages,
            ),
            OpenApiParameter(
                "start_date",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                required=False,
                description="Format: YYYY-MM-DD",
            ),
            OpenApiParameter(
                "end_date",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                required=False,
                description="Format: YYYY-MM-DD",
            ),
        ]
    )
    def list(self, request: Request) -> Response:  # noqa: C901
        """Get all the parties. Response will be paginated."""
        # if not request.user.is_superuser and not request.user.is_management:
        #     self.queryset = self.queryset.filter(created_by=request.user)
        current_user = request.user
        role = current_user.groups.first()
        has_status = request.query_params.get("status", None)
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)
        query = request.query_params.get("q", None)

        if not current_user.is_superuser:
            if current_user.is_management:
                self.queryset = self.queryset.filter(~Q(status="draft"))
            else:
                self.queryset = self.queryset.filter(Q(created_by=current_user))

        if query != '""' and query != "''" and query:
            self.queryset = self.queryset.filter(
                Q(id__iexact=query)
                | Q(witp_code__iexact=query)
                | Q(party_name__icontains=query)
                | Q(receiver_name__icontains=query)
                | Q(wo_po_mou_reference__icontains=query)
            )

        if has_status and has_status != "" and has_status != "all":
            # TODO: need to use match case for below conditions
            if has_status == StatusChoices.PENDING:
                if not role:
                    self.queryset = self.queryset.filter(
                        status=StatusChoices.PENDING
                    ).order_by("-created_at")
                else:
                    self.queryset = self.queryset.filter(
                        status=StatusChoices.PENDING,
                        stage__iexact=role.name,
                        approval_queues__status=StatusChoices.PENDING,
                        approval_queues__node__user=current_user,
                    ).distinct()
            if has_status == StatusChoices.APPROVED:
                if not role:
                    self.queryset = self.queryset.filter(
                        status=StatusChoices.APPROVED
                    ).order_by("-created_at")
                else:
                    self.queryset = self.queryset.filter(
                        Q(stage=StatusChoices.APPROVED)
                        | (
                            Q(status=StatusChoices.PENDING)
                            & Q(approval_queues__status=StatusChoices.APPROVED)
                            & Q(approval_queues__node__user=current_user)
                        )
                    ).distinct()
            if has_status == StatusChoices.REJECTED:
                self.queryset = self.queryset.filter(
                    status=StatusChoices.REJECTED
                ).order_by("-created_at")
        else:
            if role:
                self.queryset = self.queryset.filter(
                    (
                        Q(stage=StatusChoices.APPROVED)
                        | Q(stage=StatusChoices.REJECTED)
                        | (
                            Q(stage__iexact=role.name)
                            & Q(approval_queues__status=StatusChoices.PENDING)
                            & Q(approval_queues__node__user=current_user)
                        )
                        | (
                            Q(status=StatusChoices.PENDING)
                            & Q(approval_queues__status=StatusChoices.APPROVED)
                            & Q(approval_queues__node__user=current_user)
                        )
                    ),
                ).distinct()

        try:
            if start_date and end_date:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(
                    days=1
                )
                self.queryset = self.queryset.filter(
                    created_at__range=(start_datetime, end_datetime)
                )

        except ValueError as exc:
            logger.error("could not parse the given dates in url params")
            logger.exception(exc)

        paginator = self.pagination_class()
        paginator.set_page_size(request)
        paginated_queryset = paginator.paginate_queryset(
            self.queryset,
            request,
        )
        serialized_data = self.serializer_class(instance=paginated_queryset, many=True)
        return paginator.get_paginated_response(serialized_data.data)

    @extend_schema(request=ShipLocationCreateSerializer)
    def create(self, request: Request) -> Response:
        """Create new Shipment Location Change Application"""
        serialized_data = ShipLocationCreateSerializer(data=request.data)

        if not serialized_data.is_valid():
            logger.error(
                f"Validation error in ship location at create method : {str(serialized_data.errors)!r}"
            )
            raise exceptions.ValidationError(serialized_data.errors)

        # Check if the party with the provided WITP code exists
        witp_code = serialized_data.validated_data["witp_code"]
        try:
            result = fetch_basic_party(witp_code)
            if not bool(result):
                raise Http404(f"Party with WITP({witp_code!r}) not found !")
        except Http404:
            logger.error(f"Party with WITP code {witp_code} does not exist")
            raise PartyNotFoundException(  # noqa: B904
                f"Party with WITP code {witp_code} does not exist"
            )  # noqa: B904

        serialized_data.validated_data["created_by"] = request.user
        serialized_data.save()
        logger.info("Successfully created ship location.")
        return Response(
            self.serializer_class(instance=serialized_data.instance).data,
            status.HTTP_201_CREATED,
        )

    @extend_schema(request=ShipLocationCreateSerializer)
    def partial_update(self, request: Request, pk: uuid.UUID) -> Response:
        """Update a party partially"""
        try:
            credit_limit_orm = ShipLocation.objects.get(id=pk)
        except ShipLocation.DoesNotExist as e:
            logger.error(f"Ship location with id {pk!r} does not exist.")
            raise ShipLocationApplicationNotFoundException from e
        payload = ShipLocationCreateSerializer(
            instance=credit_limit_orm, data=request.data, partial=True
        )
        if not payload.is_valid():
            logger.error(f"Validation error for id {pk!r} : {str(payload.errors)!r}")
            raise exceptions.ValidationError(payload.errors)
        payload.save()
        credit_limit_serialized = self.serializer_class(instance=payload.instance)
        logger.info(f"Partially updated ship location of id {pk!r}")
        return Response(credit_limit_serialized.data)

    def retrieve(self, request: Request, pk: uuid.UUID) -> Response:
        """Retrive a single party"""
        try:
            credit_limit_orm = ShipLocation.objects.get(id=pk)
        except ShipLocation.DoesNotExist as e:
            logger.error(f"Ship location with id {pk!r} does not exist.")
            raise ShipLocationApplicationNotFoundException from e

        serialized_credit_limit = self.serializer_class(instance=credit_limit_orm)
        logger.info(f"Successfully retrived ship location of id {pk!r}.")
        return Response(serialized_credit_limit.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="witp-code",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
            )
        ]
    )
    @action(detail=False, methods=[HTTPMethod.GET], url_path="addresses")
    def get_existing_addresses(self, request: Request):
        witp_code = request.query_params.get("witp-code", "").strip()

        if not bool(witp_code):
            raise ShipLocationApplicationNotFoundException()

        return Response(
            list(ShipLocationService.get_addresses_of_party(witp_code=witp_code))
        )
