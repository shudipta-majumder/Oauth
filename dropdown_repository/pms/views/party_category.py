from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from core.openapi_metadata.metadata import OpenApiTags
from core.renderer import CustomRenderer

from ..models import BusinessTypeLov, PartyCategoryLov
from ..serializers import BusinessTypeSerializer, PartyCategorySerializer

__all__ = [
    "PartyCategoryView",
    "BusinessTypeView",
]


@extend_schema(tags=[OpenApiTags.DROPDOWN_REPO_PMS])
class PartyCategoryView(ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = PartyCategoryLov.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = PartyCategorySerializer
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            self.permission_classes = [IsAuthenticatedOrTokenHasScope, IsAdminUser]
        return [permission() for permission in self.permission_classes]

    class Meta:
        model = PartyCategoryLov


@extend_schema(tags=[OpenApiTags.DROPDOWN_REPO_PMS])
class BusinessTypeView(ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = BusinessTypeLov.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = BusinessTypeSerializer
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            self.permission_classes = [IsAuthenticatedOrTokenHasScope, IsAdminUser]
        return [permission() for permission in self.permission_classes]

    class Meta:
        model = BusinessTypeLov
