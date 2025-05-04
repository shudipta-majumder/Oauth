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
from dropdown_repository.pms.models.repository import DistrictLov, DivisionLov

from ..models import PoliceStationLov
from ..serializers import PoliceStationserializer

__all__ = [
    "PoliceStationView",
]


@extend_schema(tags=[OpenApiTags.DROPDOWN_REPO_PMS])
class PoliceStationView(ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = PoliceStationLov.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = PoliceStationserializer
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            self.permission_classes = [IsAuthenticatedOrTokenHasScope, IsAdminUser]
        return [permission() for permission in self.permission_classes]

    @action(methods=[HTTPMethod.GET], detail=True, url_path="byDivision")
    def by_division(self, request: Request, pk: int) -> Response:
        division = DivisionLov.objects.get(pk=pk)
        stations = division.policestationlov_set.all()
        serialized = self.serializer_class(instance=stations, many=True)

        return Response(serialized.data)

    @action(methods=[HTTPMethod.GET], detail=True, url_path="byDistrict")
    def by_district(self, request: Request, pk: int) -> Response:
        district = DistrictLov.objects.get(pk=pk)
        stations = district.policestationlov_set.all()
        serialized = self.serializer_class(instance=stations, many=True)

        return Response(serialized.data)

    class Meta:
        model = PoliceStationLov
