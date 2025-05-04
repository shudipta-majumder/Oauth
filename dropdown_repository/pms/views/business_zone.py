from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from core.openapi_metadata.metadata import OpenApiTags
from core.renderer import CustomRenderer

from ..models import BusinessZoneLov
from ..serializers import BusinessZoneSerializer

__all__ = [
    "BusinessZoneView",
]


@extend_schema(tags=[OpenApiTags.DROPDOWN_REPO_PMS])
class BusinessZoneView(ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = BusinessZoneLov.objects.all().order_by("-created_at")
    serializer_class = BusinessZoneSerializer
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            self.permission_classes = [IsAuthenticatedOrTokenHasScope, IsAdminUser]
        return [permission() for permission in self.permission_classes]

    class Meta:
        model = BusinessZoneLov
