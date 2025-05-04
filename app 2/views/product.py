from logging import getLogger

from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    UpdateAPIView,
)

from core.openapi_metadata.metadata import OpenApiTags
from core.permissions import UserAccessControl, UserAccessControlForAnalysisTeam
from core.renderer import CustomRenderer

from ..models.product import Product, ProductAnalysis, ProductSpacification
from ..serializers.product import (
    CustomProductSerializer,
    ProductSerializer,
)

logger = getLogger(__name__)


@extend_schema(tags=[OpenApiTags.TMS_PRODUCT])
class ProductListCreateView(ListCreateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


@extend_schema(tags=[OpenApiTags.TMS_PRODUCT])
class ProductRetrieveUpdateView(RetrieveUpdateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    lookup_url_kwarg = "pk"
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


@extend_schema(tags=[OpenApiTags.TENDER_ANALYSIS])
class ProductAnalysisCreateView(CreateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [
        UserAccessControlForAnalysisTeam,
    ]
    serializer_class = CustomProductSerializer
    renderer_classes = [CustomRenderer]
    queryset = ProductAnalysis.objects.all()
    lookup_field = "id"

    def perform_create(self, serializer):
        serializer.save()


@extend_schema(tags=[OpenApiTags.TENDER_ANALYSIS])
class ProductAnalysisUpdateView(UpdateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    serializer_class = CustomProductSerializer
    renderer_classes = [CustomRenderer]
    queryset = ProductAnalysis.objects.all()
    lookup_field = "id"

    def perform_update(self, serializer):
        serializer.save()


@extend_schema(tags=[OpenApiTags.TENDER_ANALYSIS])
class ProductSpacificationDeleteView(DestroyAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [
        UserAccessControlForAnalysisTeam,
    ]
    queryset = ProductSpacification.objects.all()
    renderer_classes = [CustomRenderer]
    lookup_field = "id"


@extend_schema(tags=[OpenApiTags.TENDER_ANALYSIS])
class ProductAnalysisDeleteView(DestroyAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [
        UserAccessControlForAnalysisTeam,
    ]
    queryset = ProductAnalysis.objects.all()
    renderer_classes = [CustomRenderer]
    lookup_field = "id"

    def perform_destroy(self, instance):
        # Get the associated product
        product = instance.product
        # Delete the ProductAnalysis instance
        super().perform_destroy(instance)
        # Set the product's is_reviewed field to False
        product.is_reviewed = False
        product.save()
