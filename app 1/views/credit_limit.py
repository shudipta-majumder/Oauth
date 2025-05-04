import uuid
from logging import getLogger

from django.contrib.auth.models import Group
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from core.constants import StatusChoices
from core.openapi_metadata.metadata import OpenApiTags
from core.pagination import StandardResultSetPagination
from core.renderer import CustomRenderer
from pms.constants import PMSRecommendationStages

from ..models import CreditLimit, CreditLimitDetail
from ..serializers import (
    CreditLimitDetailSerializer,
    CreditLimitSerializer,
)
from ..services.application_blocker import CreditLimitExpiredDocHandler

logging = getLogger("pms.views.credit_limit")

ALLOWED_TYPE = ["jpg", "jpeg", "pdf", "png"]


def is_incharge(role: Group) -> bool:
    if not role:
        return False
    return role.name.lower() == PMSRecommendationStages.INCHARGE.value.lower()


def find_allowed_type(input_string):
    for file_type in ALLOWED_TYPE:
        if (
            file_type in input_string.lower()
        ):  # Convert both strings to lowercase for case-insensitive comparison
            return file_type
    return None  # Return None if no allowed type is found in the input string


__all__ = ["CreditLimitViewSet", "CreditLimitDetailViewSet"]


class CreditLimitApplicationNotFoundException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Application does not exists.")
    default_code = "not_found"


class RoleNotDefinedException(exceptions.APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("User Role Not Defined.")
    default_code = "not_found"


@extend_schema(tags=[OpenApiTags.PMS_CREDIT_LIMIT_APPLICATION])
class CreditLimitViewSet(ViewSet):
    queryset = CreditLimit.objects.all().order_by("-created_at")
    serializer_class = CreditLimitSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    pagination_class = StandardResultSetPagination
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def _send_paginate_response(self, request, queryset):
        paginator = self.pagination_class()
        paginator.set_page_size(request)
        qs = paginator.paginate_queryset(
            queryset,
            request,
        )
        serialized_data = self.serializer_class(instance=qs, many=True)
        return paginator.get_paginated_response(serialized_data.data)

    @staticmethod
    def _filter_by_query(queryset, query: str):
        """Filter queryset based on search query."""
        if query and query not in ('""', "''", ""):
            return CreditLimit().filter_by_text(queryset, query)
        return queryset

    def _filter_by_user_role(self, user):
        """Filter queryset based on user role."""
        if not user.is_superuser:
            if user.is_management:
                return self.queryset.filter(~Q(status=StatusChoices.DRAFT))
            return self.queryset.filter(created_by=user)
        return self.queryset

    @staticmethod
    def _filter_by_status(queryset, app_status, user):
        """Filter queryset based on status."""
        if app_status and app_status != "all" and app_status not in ('""', "''", ""):
            return CreditLimit().filter_by_status(queryset, app_status, user)
        return queryset

    @staticmethod
    def _filter_by_date_range(queryset, start_date, end_date):
        """Filter queryset based on date range."""
        if start_date and end_date:
            try:
                return CreditLimit().filter_by_created_on_range(
                    queryset, start_date, end_date
                )
            except ValueError as exc:
                logging.error("Could not parse the given dates in URL params")
                logging.exception(exc)
                raise exceptions.ValidationError(
                    "Invalid date format given in URL params."
                ) from exc
        return queryset

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
    def list(self, request: Request) -> Response:
        """Get all the parties. Response will be paginated."""
        current_user = request.user

        # role wise filtering
        queryset = self._filter_by_user_role(current_user)

        # query filtering
        query = request.query_params.get("q")
        queryset = self._filter_by_query(queryset, query)

        # status filtering
        has_status = request.query_params.get("status")
        queryset = self._filter_by_status(queryset, has_status, current_user)

        # date range filtering
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        queryset = self._filter_by_date_range(queryset, start_date, end_date)

        return self._send_paginate_response(request, queryset)

    @extend_schema(request=CreditLimitSerializer)
    def create(self, request: Request) -> Response:
        """Create new Credit Limit"""
        serialized_data = CreditLimitSerializer(data=request.data)
        blocker = CreditLimitExpiredDocHandler()

        if not serialized_data.is_valid():
            logging.error(
                f"Validation error at credit limit create method: {str(serialized_data.errors)}"
            )
            raise exceptions.ValidationError(serialized_data.errors)

        blocker.run_check(serialized_data.validated_data.get("witp_code"))

        serialized_data.validated_data["created_by"] = request.user
        serialized_data.save()

        logging.info("successfully create credit limit.")
        return Response(serialized_data.data, status.HTTP_201_CREATED)

    @extend_schema(request=CreditLimitSerializer)
    def partial_update(self, request: Request, pk: uuid.UUID) -> Response:
        """Update a Limit partially"""
        try:
            orm_instance = CreditLimit.objects.get(id=pk)
        except CreditLimit.DoesNotExist as e:
            logging.error(f"Credit limit with {pk!r} is not exist.")
            raise CreditLimitApplicationNotFoundException from e

        serialized_instance = self.serializer_class(
            instance=orm_instance, data=request.data, partial=True
        )

        if not serialized_instance.is_valid():
            logging.error(
                f"Validation error at credit limit create method: {str(serialized_instance.errors)}"
            )
            raise exceptions.ValidationError(serialized_instance.errors)

        serialized_instance.validated_data["updated_by"] = request.user
        serialized_instance.save()

        logging.info(f"Credit limit with id {pk!r} partially updated.")
        return Response(serialized_instance.data)

    def retrieve(self, request: Request, pk: uuid.UUID) -> Response:
        """Retrieve a single party"""
        try:
            orm_instance = CreditLimit.objects.get(id=pk)
        except CreditLimit.DoesNotExist as e:
            logging.error(f"Credit limit with id {pk!r} does not exist.")
            raise CreditLimitApplicationNotFoundException from e

        serialized_credit_limit = self.serializer_class(instance=orm_instance)
        logging.info(f"Credit limit with id {pk!r} retrieved successfully.")
        return Response(serialized_credit_limit.data)

    def destroy(self, request: Request, pk: uuid.UUID) -> Response:
        try:
            orm_instance = self.queryset.get(id=pk)
        except CreditLimit.DoesNotExist as exc:
            logging.error(f"Credit limit with {pk!r} is not exist.")
            raise CreditLimitApplicationNotFoundException from exc
        orm_instance.delete()
        return Response(None, status=status.HTTP_200_OK)


@extend_schema(tags=[OpenApiTags.PMS_CREDIT_LIMIT_DETAIL_APPLICATION])
class CreditLimitDetailViewSet(ModelViewSet):
    queryset = CreditLimitDetail.objects.all().order_by("id")
    serializer_class = CreditLimitDetailSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    pagination_class = None
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        try:
            orm_instance = self.get_object()
        except CreditLimit.DoesNotExist as exc:
            logging.exception(exc)
            raise CreditLimitApplicationNotFoundException from exc
        orm_instance.delete()
        return Response(None, status=status.HTTP_200_OK)
