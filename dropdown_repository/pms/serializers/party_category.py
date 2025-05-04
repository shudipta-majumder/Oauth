from rest_framework.serializers import ModelSerializer

from core.constants import EXCLUDE_FIELDS

from ..models import BusinessTypeLov, PartyCategoryLov

__all__ = [
    "PartyCategorySerializer",
    "BusinessTypeSerializer",
]


class PartyCategorySerializer(ModelSerializer):
    class Meta:
        model = PartyCategoryLov
        exclude = EXCLUDE_FIELDS


class BusinessTypeSerializer(ModelSerializer):
    class Meta:
        model = BusinessTypeLov
        exclude = EXCLUDE_FIELDS

    def to_representation(self, instance: BusinessTypeLov):
        response = super().to_representation(instance)

        response["business_types"] = PartyCategorySerializer(
            instance.business_types.all(), many=True
        ).data

        return response
