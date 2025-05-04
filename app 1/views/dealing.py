import uuid
from logging import getLogger

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
from rest_framework.viewsets import ViewSet

from core.openapi_metadata.metadata import OpenApiTags
from core.pagination import StandardResultSetPagination
from core.renderer import CustomRenderer
from pms.models.party import Party

from ..models import PartyDealing
from ..serializers import DealingSerializer

logger = getLogger("pms.views.dealing")


__all__ = ["DealingViewSet"]


class PartyDealingFoundException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Dealing item does not exists.")
    default_code = "dealing_error"


@extend_schema(tags=[OpenApiTags.DEALINGS])
class DealingViewSet(ViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = PartyDealing.objects.all()
    serializer_class = DealingSerializer
    pagination_class = StandardResultSetPagination
    paginator = StandardResultSetPagination()
    required_scopes = ["read"]
    renderer_classes = [
        CustomRenderer,
    ]

    def list(self, request: Request) -> Response:
        self.paginator.set_page_size(request)
        paginated_queryset = self.paginator.paginate_queryset(self.queryset, request)
        serialized_queryset = self.serializer_class(
            instance=paginated_queryset, many=True
        )

        return self.paginator.get_paginated_response(serialized_queryset.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="step",
                type=OpenApiTypes.NUMBER,
                location=OpenApiParameter.QUERY,
                required=False,
            )
        ],
    )
    def partial_update(self, request: Request, pk: uuid.UUID) -> Response:
        try:
            dealing = PartyDealing.objects.get(id=pk)
        except PartyDealing.DoesNotExist as exc:
            raise PartyDealingFoundException from exc

        serialized_dealing = DealingSerializer(
            instance=dealing, data=request.data, partial=True
        )

        if not serialized_dealing.is_valid():
            raise exceptions.ValidationError(str(serialized_dealing.errors))

        serialized_dealing.save()
        query_param = request.query_params.get("step", None)

        if query_param and query_param != "null" and query_param != "":
            # Side Effect as hardcore frontend doesn't have the ablity to call API.
            party = Party.objects.get(id=dealing.party.id)
            party.stepper_index = query_param
            party.save()

        return Response(self.serializer_class(dealing).data, status.HTTP_200_OK)
