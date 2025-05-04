from logging import getLogger

from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from core.openapi_metadata.metadata import OpenApiTags
from core.pagination import StandardResultSetPagination
from core.permissions import UserAccessControl
from core.renderer import CustomRenderer

from ..models.notification import Notification
from ..serializers.notification import NotificationSerializer

logger = getLogger(__name__)


@extend_schema(tags=[OpenApiTags.NOTIFICATION])
class NotificationViews(ListAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


class BaseNotificationListView(ListAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    serializer_class = NotificationSerializer
    renderer_classes = [CustomRenderer]
    pagination_class = StandardResultSetPagination
    notification_type = None
    filter_backends = [SearchFilter]
    search_fields = [
        "tender_id_ref",
        "team_name",
        "tender_type",
        "procurring_entity",
        "kam_name",
        "notification_type",
        "remaining_time",
    ]

    def get(self, request, *args, **kwargs):
        self.pagination_class.page_size = 10
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Notification.objects.all()
        if self.notification_type:
            if isinstance(self.notification_type, list):
                queryset = queryset.filter(notification_type__in=self.notification_type)
            else:
                queryset = queryset.filter(notification_type=self.notification_type)
        queryset = queryset.order_by("remaining_time")
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        notification_counts = {
            "bg_pg_validity": Notification.objects.filter(
                notification_type__in=["BG", "PG"]
            ).count(),
            "noa_acceptance_deadline": Notification.objects.filter(
                notification_type="NOA ACCEPTANCE DEADLINE"
            ).count(),
            "contract_agreement_deadline": Notification.objects.filter(
                notification_type="CONTRACT AGREEMENT DEADLINE"
            ).count(),
            "completion_certificate": Notification.objects.filter(
                notification_type="COMPLETION CERTIFICATE"
            ).count(),
            "delivery_deadline": Notification.objects.filter(
                notification_type="DELIVERY DEADLINE"
            ).count(),
        }

        # Apply pagination to the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Serialize the paginated data
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)

            # Add the counts to the paginated response
            paginated_response.data.update({"notification_count": notification_counts})
            return paginated_response

        # If pagination is not applied, serialize the entire queryset
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "notifications": serializer.data,
                "notification_count": notification_counts,
            }
        )


@extend_schema(tags=[OpenApiTags.NOTIFICATION])
class BgPgNotificationListView(BaseNotificationListView):
    notification_type = ["BG", "PG"]


@extend_schema(tags=[OpenApiTags.NOTIFICATION])
class NoaAcceptanceDeadlineNotificationListView(BaseNotificationListView):
    notification_type = "NOA ACCEPTANCE DEADLINE"


@extend_schema(tags=[OpenApiTags.NOTIFICATION])
class ContractAgreementDeadlineNotificationListView(BaseNotificationListView):
    notification_type = "CONTRACT AGREEMENT DEADLINE"


@extend_schema(tags=[OpenApiTags.NOTIFICATION])
class CompletionCertificateNotificationListView(BaseNotificationListView):
    notification_type = "COMPLETION CERTIFICATE"


@extend_schema(tags=[OpenApiTags.NOTIFICATION])
class DeliveryDeadlineNotificationListView(BaseNotificationListView):
    notification_type = "DELIVERY DEADLINE"
