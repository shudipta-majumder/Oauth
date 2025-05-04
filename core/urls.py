from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.settings import api_settings

api_v1 = "api/v1"

urlpatterns = [
    path("admin/", admin.site.urls),
    # oauth2 urls
    path("oauth2/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    # auth-users urls
    path(f"{api_v1}/auth/", include("auth_users.urls")),
    # Open API & Swagger UI
    path(
        "api/openapi",
        SpectacularAPIView.as_view(
            renderer_classes=api_settings.DEFAULT_RENDERER_CLASSES
        ),
        name="openapi",
    ),
    path(
        "api/docs",
        SpectacularSwaggerView.as_view(url_name="openapi"),
        name="swagger-ui",
    ),
    path("api/redoc", SpectacularRedocView.as_view(url_name="openapi"), name="redoc"),
    path(
        "",
        SpectacularSwaggerView.as_view(url_name="openapi"),
        name="swagger-ui",
    ),
    # dropdown_repository
    path(f"{api_v1}/dr/", include("dropdown_repository.urls")),
    # Digital Party Management System
    path(f"{api_v1}/pms/", include("pms.urls")),
    # Recommendation Engine URLS
    path(f"{api_v1}/queues/", include("recommendation_engine.urls")),
    # Menu URL
    path(f"{api_v1}/menus/", include("menu.urls")),
    #TMS URL
    path(f"{api_v1}/tms/",include("tms.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
