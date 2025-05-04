from rest_framework.serializers import ModelSerializer

from core.constants import EXCLUDE_FIELDS

from ..models import BusinessZoneLov

__all__ = [
    "BusinessZoneSerializer",
]


class BusinessZoneSerializer(ModelSerializer):
    class Meta:
        model = BusinessZoneLov
        exclude = EXCLUDE_FIELDS
