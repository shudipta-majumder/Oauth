from rest_framework.serializers import ModelSerializer, UUIDField

from auth_users.serializers import UserSerializer
from core.constants import EXCLUDE_FIELDS
from recommendation_engine.serializers import ApprovalQueueSerializer

from ..models import ShipLocation

__all__ = ["ShipLocationSerializer", "ShipLocationCreateSerializer"]


class ShipLocationCreateSerializer(ModelSerializer):
    class Meta:
        model = ShipLocation
        exclude = EXCLUDE_FIELDS


class ShipLocationSerializer(ModelSerializer):
    id = UUIDField(required=False, allow_null=True)
    marketing_concern = UserSerializer()
    approval_queues = ApprovalQueueSerializer(many=True, read_only=True)

    class Meta:
        model = ShipLocation
        fields = "__all__"

    def to_representation(self, instance: ShipLocation):
        payload = super().to_representation(instance)
        payload["created_by"] = UserSerializer(instance=instance.created_by).data
        payload["updated_by"] = UserSerializer(instance=instance.created_by).data
        return payload
