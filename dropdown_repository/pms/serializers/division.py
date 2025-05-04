from rest_framework.serializers import ModelSerializer

from core.constants import EXCLUDE_FIELDS

from ..models import DivisionLov

__all__ = [
    "DivisionSerializer",
]


class DivisionSerializer(ModelSerializer):
    class Meta:
        model = DivisionLov
        exclude = EXCLUDE_FIELDS
