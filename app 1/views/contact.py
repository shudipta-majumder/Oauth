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
from pms.constants import EXISTING_PARTY

from ..models import Contact
from ..serializers import ContactSerializer

__all__ = ["ContactViewSet"]


class ForbiddenException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("forbidden action !")
    default_code = "contact_error"


@extend_schema(tags=[OpenApiTags.CONTACTS])
class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    pagination_class = StandardResultSetPagination
    renderer_classes = (CustomRenderer,)
    required_scopes = ["read"]

    def destroy(self, request: Request, pk: int) -> Response:
        obj = Contact.objects.get(pk=pk)
        if obj.party.process == EXISTING_PARTY:
            raise ForbiddenException(
                detail=f"delete action is forbidden not for party=(${obj.party!r})"
            )
        obj.delete()
        return Response(None, status=status.HTTP_200_OK)
