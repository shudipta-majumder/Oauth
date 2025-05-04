from django.urls import include, path
from rest_framework import routers

from .views import AccountViewSet, UserViewSet

router = routers.DefaultRouter()
router.register("users", UserViewSet)
router.register("accounts", AccountViewSet, basename="accounts")

urlpatterns = [
    path("", include(router.urls)),
]
