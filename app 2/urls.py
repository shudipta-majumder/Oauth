from django.urls import path

from .views.bg_vaidity_date import BGValidityDateListCreateView
from .views.contract_agreement import (
    ContractAgreementCreateView,
    ContractAgreementUpdateView,
    PaymentCreateView,
    PaymentDeleteAPIView,
    PaymentUpdateAPIView,
    VendorCreateView,
    VendorDeleteAPIView,
    VendorUpdateAPIView,
)
from .views.noa import NoaListCreateView, NoaUpdateView
from .views.notification import (
    BgPgNotificationListView,
    CompletionCertificateNotificationListView,
    ContractAgreementDeadlineNotificationListView,
    DeliveryDeadlineNotificationListView,
    NoaAcceptanceDeadlineNotificationListView,
    NotificationViews,
)
from .views.product import (
    ProductAnalysisCreateView,
    ProductAnalysisDeleteView,
    ProductAnalysisUpdateView,
    ProductListCreateView,
    ProductRetrieveUpdateView,
    ProductSpacificationDeleteView,
)

# ProductSpacificationUpdateView,
from .views.setup import (
    MinistryListAPI,
    ParticipantsListAPI,
    TeamListAPI,
    TenderTypeListAPI,
)
from .views.tender import (
    CompleteTenderListView,
    OnGoingTenderListView,
    TenderAnalysisView,
    TenderListCreateView,
    TenderPostSubmission,
    TenderUpdateView,
)

urlpatterns = [
    # Setup view's urls
    path("team-list/", TeamListAPI.as_view(), name="team-list"),
    path("ministry-list/", MinistryListAPI.as_view(), name="ministry-list"),
    path("tendertype-list/", TenderTypeListAPI.as_view(), name="tendertype-list"),
    path("participant-list/", ParticipantsListAPI.as_view(), name="participant-list"),
    # Product view's urls
    path("products/", ProductListCreateView.as_view(), name="product-list-create"),
    path(
        "products/<uuid:pk>/",
        ProductRetrieveUpdateView.as_view(),
        name="product-retrieve-update",
    ),
    # Tender view's urls
    path("tender/", TenderListCreateView.as_view(), name="tender-list-create"),
    path(
        "tender/<uuid:id>/",
        TenderListCreateView.as_view(),
        name="individual-tender-detail",
    ),
    path(
        "tender/complete-tenders/",
        CompleteTenderListView.as_view(),
        name="complete_tender_list",
    ),
    path(
        "tender/ongoing-tender/",
        OnGoingTenderListView.as_view(),
        name="ongoing_tender_list",
    ),
    # bg-extended-date urls
    path(
        "bg-valid-date/",
        BGValidityDateListCreateView.as_view(),
        name="bg-valid-date-list-create",
    ),
    # Pre-tender meeting urls
    path(
        "tender/presubmission/<str:id>/",
        TenderUpdateView.as_view(),
        name="tender-update",
    ),
    path(
        "tender/postsubmission/<str:id>/",
        TenderPostSubmission.as_view(),
        name="tender_post_submission",
    ),
    # Noa urls
    path("tender/noa/", NoaListCreateView.as_view(), name="noa-list-create"),
    path(
        "tender/noa/<str:id>/",
        NoaUpdateView.as_view(),
        name="noa-update",
    ),
    # Contract Agreement urls
    path(
        "tender/contract-agreement/",
        ContractAgreementCreateView.as_view(),
        name="contract-agreement",
    ),
    path(
        "tender/contract-agreement/<str:id>/",
        ContractAgreementUpdateView.as_view(),
        name="contract-agreement-update",
    ),
    # Notification urls
    path("notifications", NotificationViews.as_view(), name="NotificationViews"),
    path(
        "tender/bg-pg-notification/",
        BgPgNotificationListView.as_view(),
        name="bg_pg_notification",
    ),
    path(
        "tender/noa-acceptance-deadline-notification/",
        NoaAcceptanceDeadlineNotificationListView.as_view(),
        name="noa_acceptance_deadline_notification",
    ),
    path(
        "tender/contract-agreement-deadline-notification/",
        ContractAgreementDeadlineNotificationListView.as_view(),
        name="contract_agreement_deadline_notification",
    ),
    path(
        "tender/completion-certificate-notification/",
        CompletionCertificateNotificationListView.as_view(),
        name="completion_certificate_notification",
    ),
    path(
        "tender/delivery-deadline-notification/",
        DeliveryDeadlineNotificationListView.as_view(),
        name="delivery_deadline_notification",
    ),
    # Vendor urls
    path("tender/create-vendor/", VendorCreateView.as_view(), name="VendorCreateView"),
    path(
        "tender/update-vendor/<str:id>/",
        VendorUpdateAPIView.as_view(),
        name="VendorUpdateAPIView",
    ),
    path(
        "tender/delete-vendor/<str:id>/",
        VendorDeleteAPIView.as_view(),
        name="VendorDeleteAPIView",
    ),
    # Payments urls
    path(
        "tender/create-payment/",
        PaymentCreateView.as_view(),
        name="payment_create_view",
    ),
    path(
        "tender/update-payment/<str:id>/",
        PaymentUpdateAPIView.as_view(),
        name="payment_update_view",
    ),
    path(
        "tender/delete-payment/<str:id>/",
        PaymentDeleteAPIView.as_view(),
        name="payment_delete_view",
    ),
    # BI team urls
    path(
        "tender/analysis/<str:id>",
        TenderAnalysisView.as_view(),
        name="tender_analysis_view",
    ),
    path(
        "tender/product/analysis/",
        ProductAnalysisCreateView.as_view(),
        name="product_analysis_create_update",
    ),
    path(
        "tender/product/analysis/update/<str:id>/",
        ProductAnalysisUpdateView.as_view(),
        name="product_analysis_update",
    ),
    path(
        "tender/product/spacification/delete/<str:id>",
        ProductSpacificationDeleteView.as_view(),
        name="product_spacification_delete",
    ),
    path(
        "tender/product/analysis/delete/<str:id>/",
        ProductAnalysisDeleteView.as_view(),
        name="product_analysis_delete",
    ),
]
