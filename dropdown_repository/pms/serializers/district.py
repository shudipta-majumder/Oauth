from rest_framework.serializers import ModelSerializer

from core.constants import EXCLUDE_FIELDS

from ..models import DistrictLov

__all__ = [
    "DistrictSerializer",
]


class DistrictSerializer(ModelSerializer):
    class Meta:
        model = DistrictLov
        exclude = EXCLUDE_FIELDS
