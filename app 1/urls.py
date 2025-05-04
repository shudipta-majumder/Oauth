from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AttachmentRepoViewSet,
    AttachmentViewSet,
    ContactViewSet,
    CreditLimitDetailViewSet,
    CreditLimitViewSet,
    DealingViewSet,
    EbsPartyCollectionViewSet,
    EbsPartyViewSet,
    ExtraAttachmentViewSet,
    GuaranteeViewSet,
    PartyViewSet,
    SecurityChequeViewSet,
    ShipLocationViewSet,
)

pms_router = DefaultRouter()

pms_router.register(
    "registrations/parties",
    PartyViewSet,
    basename="pmsregister",
)
pms_router.register("registrations/dealings", DealingViewSet, basename="pmsdealing")
pms_router.register(
    "registrations/cheques", SecurityChequeViewSet, basename="pmscheques"
)
pms_router.register(
    "registrations/guarantees", GuaranteeViewSet, basename="pmsguarantees"
)
pms_router.register(
    "registrations/attachments/repo",
    AttachmentRepoViewSet,
    basename="pmsattachmentsrepo",
)
pms_router.register(
    "registrations/extra",
    ExtraAttachmentViewSet,
    basename="pms-extra-attachment",
)
pms_router.register(
    "registrations/attachments", AttachmentViewSet, basename="pmsattachments"
)
pms_router.register("registrations/contacts", ContactViewSet, basename="pmscontacts")
pms_router.register("ebs", EbsPartyViewSet, basename="ebs")
pms_router.register(
    "creditlimits/details", CreditLimitDetailViewSet, basename="creditlimitdetails"
)
pms_router.register("creditlimits", CreditLimitViewSet, basename="creditlimits")
pms_router.register("shiplocations", ShipLocationViewSet, basename="shiplocations")
pms_router.register(
    "partycollection", EbsPartyCollectionViewSet, basename="partycollection"
)

urlpatterns = [
    path(
        "",
        include(pms_router.urls),
    ),
]
