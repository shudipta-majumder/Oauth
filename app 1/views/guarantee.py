from logging import getLogger

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.openapi_metadata.metadata import OpenApiTags
from core.pagination import StandardResultSetPagination
from core.renderer import CustomRenderer

from ..models import Guarantee
from ..serializers import GuaranteeSerializer

logger = getLogger("pms.views.guarantee")


__all__ = ["GuaranteeViewSet"]


class GuranteeObjectDoesNotExistException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("security cheque does not exists.")
    default_code = "security_cheque_error"


@extend_schema(tags=[OpenApiTags.GUARANTOR])
class GuaranteeViewSet(ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    serializer_class = GuaranteeSerializer
    pagination_class = StandardResultSetPagination
    paginator = StandardResultSetPagination()
    required_scopes = ["read"]
    renderer_classes = [
        CustomRenderer,
    ]

    def destroy(self, request: Request, pk: int) -> Response:
        try:
            obj = Guarantee.objects.get(pk=pk)
            obj.delete()
        except Guarantee.DoesNotExist as exc:
            logger.error(f"Security Cheque Not found with id={pk!r}")
            raise GuranteeObjectDoesNotExistException from exc
        return Response(None, status=status.HTTP_200_OK)

    def get_queryset(self):
        return Guarantee.objects.all()

    class Meta:
        model = Guarantee
