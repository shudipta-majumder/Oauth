from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework.generics import ListCreateAPIView, UpdateAPIView

from core.openapi_metadata.metadata import OpenApiTags
from core.permissions import UserAccessControl
from core.renderer import CustomRenderer

from ..models.noa import NotificationOfAward
from ..models.tender import Tender
from ..serializers.noa import NoaSerializer
from ..utils import parse_json_data


@extend_schema(tags=[OpenApiTags.POST_NOA])
class NoaListCreateView(ListCreateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    renderer_classes = [
        CustomRenderer,
    ]
    queryset = NotificationOfAward.objects.all()
    serializer_class = NoaSerializer

    def perform_create(self, serializer):
        bg_released_dates = parse_json_data(
            self.request.data.get("bg_released_date", "[]"), "BG Release date."
        )
        mapped_bg_date = []
        for bg_date in bg_released_dates:
            tender_uuid = bg_date.get("tender")
            tender_instance = get_object_or_404(Tender, id=tender_uuid)
            mapped_date = {
                "date": bg_date.get("date"),
                "is_bg_released": bg_date.get("isBgReleased"),
                "tender": tender_instance,
            }
            mapped_bg_date.append(mapped_date)
        serializer.save(bg_released_date=mapped_bg_date)


@extend_schema(tags=[OpenApiTags.POST_NOA])
class NoaUpdateView(UpdateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    renderer_classes = [
        CustomRenderer,
    ]
    queryset = NotificationOfAward.objects.all()
    serializer_class = NoaSerializer
    lookup_field = "id"

    def get_queryset(self):
        id = self.kwargs.get("id")
        noa = NotificationOfAward.objects.filter(id=id)
        return noa

    def perform_update(self, serializer):
        bg_released_dates = parse_json_data(
            self.request.data.get("bg_released_date", "[]"), "BG Release date."
        )
        mapped_bg_date = []
        for bg_date in bg_released_dates:
            tender_uuid = bg_date.get("tender")
            tender_instance = get_object_or_404(Tender, id=tender_uuid)
            mapped_date = {
                "date": bg_date.get("date"),
                "is_bg_released": bg_date.get("isBgReleased"),
                "tender": tender_instance,
            }
            mapped_bg_date.append(mapped_date)
        serializer.save(bg_released_date=mapped_bg_date)
