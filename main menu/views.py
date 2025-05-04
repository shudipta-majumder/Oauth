from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from auth_users.models import User
from core.openapi_metadata.metadata import OpenApiTags
from core.renderer import CustomRenderer

from .models import Menu
from .serializers import MenuSerializer

CACHING_TIME = 30  # 30 Seconds


@extend_schema(tags=[OpenApiTags.MENU_ROUTES])
class MenuViewSet(ViewSet):
    serializer_class = MenuSerializer
    renderer_classes = [CustomRenderer]
    authentication_classes = [OAuth2Authentication]
    pagination_class = None
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _get_root_menus():
        return (
            Menu.objects.filter(parent_menu__isnull=True)
            .prefetch_related("submenus")
            .order_by("order")
        )

    def get_queryset(self):
        return self._get_root_menus()

    @staticmethod
    def _fetch_user_menus(current_user: User):
        return Menu.objects.filter(
            parent_menu__isnull=True, is_active=True, roles__in=current_user.roles.all()
        )

    @method_decorator(cache_page(CACHING_TIME))
    @method_decorator(vary_on_headers(settings.HEADER_AUTH_KEY))
    def list(self, request: Request):
        current_user: User = request.user
        serialized = self.serializer_class(
            self._fetch_user_menus(current_user), many=True
        )
        return Response(serialized.data)

    class Meta:
        model = Menu
