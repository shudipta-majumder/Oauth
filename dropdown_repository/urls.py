from django.urls import include, path
from rest_framework.routers import DefaultRouter

from dropdown_repository.pms.views import (
    BankIssuerView,
    BranchIssuerView,
    BusinessTypeView,
    BusinessZoneView,
    DistrictViewSet,
    DivisionViewSet,
    PartyCategoryView,
    PoliceStationView,
)

dr_routes = DefaultRouter()

# PMS ROUTES (Digital Party Management System)
dr_routes.register("businesszones", BusinessZoneView, basename="businesszones")
dr_routes.register("partycategories", PartyCategoryView, basename="partycategories")
dr_routes.register("business-types", BusinessTypeView, basename="business-types")
dr_routes.register("policestations", PoliceStationView, basename="policestations")
dr_routes.register("banks", BankIssuerView, basename="bank")
dr_routes.register("branches", BranchIssuerView, basename="branches")
dr_routes.register("divisions", DivisionViewSet, basename="divisions")
dr_routes.register("districts", DistrictViewSet, basename="districts")

# GMS ROUTES

urlpatterns = [path("pms/", include(dr_routes.urls))]
