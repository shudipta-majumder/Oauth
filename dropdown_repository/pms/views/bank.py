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

from ..models import BankIssuerLov, BranchIssuerBankLov
from ..serializers import (
    BankIssuerSerializer,
    BranchIssuerSerializer,
)

__all__ = [
    "BankIssuerView",
    "BranchIssuerView",
]


@extend_schema(tags=[OpenApiTags.DROPDOWN_REPO_PMS, OpenApiTags.DROPDOWN_REPO_PMS_BANK])
class BankIssuerView(ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = BankIssuerLov.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = BankIssuerSerializer
    renderer_classes = (CustomRenderer,)
    required_scopes = ["read"]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            self.permission_classes = [IsAuthenticatedOrTokenHasScope, IsAdminUser]
        return [permission() for permission in self.permission_classes]

    class Meta:
        model = BankIssuerLov


@extend_schema(tags=[OpenApiTags.DROPDOWN_REPO_PMS, OpenApiTags.DROPDOWN_REPO_PMS_BANK])
class BranchIssuerView(ModelViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = BranchIssuerBankLov.objects.filter(is_active=True).order_by(
        "-created_at"
    )
    serializer_class = BranchIssuerSerializer
    renderer_classes = (CustomRenderer,)
    required_scopes = ["read"]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            self.permission_classes = [IsAuthenticatedOrTokenHasScope, IsAdminUser]
        return [permission() for permission in self.permission_classes]

    @action(methods=[HTTPMethod.GET], detail=True, url_path="byBank")
    def by_bank(self, request: Request, pk: int) -> Response:
        bank = BankIssuerLov.objects.get(pk=pk)
        section = bank.branchissuerbanklov_set.all()
        serialized = self.serializer_class(instance=section, many=True)

        return Response(serialized.data)

    class Meta:
        model = BranchIssuerBankLov
