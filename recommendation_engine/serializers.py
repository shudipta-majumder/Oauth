from rest_framework.serializers import ModelSerializer

from auth_users.serializers import UserSerializer
from core.constants import EXCLUDE_FIELDS

from .models import ApprovalQueue, ApprovalStep, ApprovalUser


class ApprovalStepSerializer(ModelSerializer):
    class Meta:
        model = ApprovalStep
        exclude = EXCLUDE_FIELDS


class ApprovalUserSerializer(ModelSerializer):
    approval_step = ApprovalStepSerializer()
    user = UserSerializer()

    class Meta:
        model = ApprovalUser
        exclude = EXCLUDE_FIELDS


class ApprovalQueueSerializer(ModelSerializer):
    node = ApprovalUserSerializer()

    class Meta:
        model = ApprovalQueue
        fields = "__all__"


class ApprovalUpdateSerializer(ModelSerializer):
    class Meta:
        model = ApprovalQueue
        fields = ("status", "remarks")
