from http import HTTPMethod

from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.openapi_metadata.metadata import OpenApiTags
from core.renderer import CustomRenderer
from dropdown_repository.pms.serializers.district import DistrictSerializer

from ..models import DivisionLov
from ..serializers import DivisionSerializer

__all__ = [
    "DivisionViewSet",
]


@extend_schema(tags=[OpenApiTags.DROPDOWN_REPO_PMS])
class DivisionViewSet(ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = DivisionLov.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = DivisionSerializer
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    @action(methods=[HTTPMethod.GET], detail=True)
    def districts(self, request: Request, pk: int) -> Response:
        division = DivisionLov.objects.get(pk=pk)
        districts = division.districtlov_set.all()
        serialized = DistrictSerializer(instance=districts, many=True)

        return Response(serialized.data)

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            self.permission_classes = [IsAuthenticatedOrTokenHasScope, IsAdminUser]
        return [permission() for permission in self.permission_classes]

    class Meta:
        model = DivisionLov
