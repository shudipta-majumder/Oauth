from rest_framework.serializers import ModelSerializer

from core.constants import EXCLUDE_FIELDS

from ..models import PoliceStationLov

__all__ = [
    "PoliceStationserializer",
]


class PoliceStationserializer(ModelSerializer):
    class Meta:
        model = PoliceStationLov
        exclude = EXCLUDE_FIELDS
