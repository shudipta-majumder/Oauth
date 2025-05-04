from logging import getLogger
from typing import Dict

from drf_spectacular.utils import extend_schema_field
from rest_framework.serializers import (
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from auth_users.serializers import UserSerializer
from core.constants import StatusChoices
from dropdown_repository.pms.serializers.district import DistrictSerializer
from dropdown_repository.pms.serializers.division import DivisionSerializer
from dropdown_repository.pms.serializers.party_category import PartyCategorySerializer
from dropdown_repository.pms.serializers.police_station import PoliceStationserializer
from recommendation_engine.serializers import ApprovalQueueSerializer

from ..models import Party
from ..services.application_blocker import CreditLimitExpiredDocHandler
from .attachment import AttachmentSerializer, ExtraSerializer
from .contact import (
    ContactSerializer,
)
from .dealing import DealingSerializer, GuaranteeSerializer, SecurityChequeSerializer

__all__ = ["PartySerializer", "PartyTrailSerializer"]

_logger = getLogger(__name__)


class PartySerializer(ModelSerializer):
    dealing = DealingSerializer(read_only=True)
    attachments = SerializerMethodField(read_only=True)
    security_cheques = SecurityChequeSerializer(many=True, read_only=True)
    guarantee_collections = GuaranteeSerializer(many=True, read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    approval_queues = ApprovalQueueSerializer(many=True, read_only=True)

    has_history = SerializerMethodField()
    pending_count = SerializerMethodField()
    doc_expired = SerializerMethodField()

    @extend_schema_field(AttachmentSerializer)
    def get_attachments(self, obj: Party):
        return AttachmentSerializer(instance=obj.attachments.first()).data

    def to_representation(self, instance: Party):
        response = super().to_representation(instance)

        serialized_keys: Dict[str, Serializer] = {
            "division": DivisionSerializer(instance=instance.division),
            "district": DistrictSerializer(instance=instance.district),
            "party_category": PartyCategorySerializer(instance=instance.party_category),
            "police_station": PoliceStationserializer(instance=instance.police_station),
            "sales_person": UserSerializer(instance=instance.sales_person),
            "created_by": UserSerializer(instance=instance.created_by),
            "updated_by": UserSerializer(instance=instance.updated_by),
        }
        for key, value in serialized_keys.items():
            response[key] = value.data

        response["extras"] = ExtraSerializer(instance=instance.extras, many=True).data
        return response

    def get_has_history(self, instance: Party):
        history_count = instance.rev_nodes.count()
        return history_count

    def get_pending_count(self, instance: Party):
        return instance.rev_nodes.filter(status=StatusChoices.PENDING).count()

    def get_doc_expired(self, instance: Party) -> dict:
        """this attribute is totally for credit limit application requirement !!!"""
        if instance.witp_code and instance.status == StatusChoices.APPROVED:
            expired_docs = CreditLimitExpiredDocHandler(instance=instance)
            result_set = expired_docs.export_for_ui(instance.witp_code)
            expired_cheques = result_set.get("expired_cheques", [])
            expired_guarantors = result_set.get("expired_guarantors", [])
            cheques = []
            guarantors = []
            if expired_cheques:
                cheques = SecurityChequeSerializer(expired_cheques, many=True).data
            if expired_guarantors:
                guarantors = GuaranteeSerializer(expired_guarantors, many=True).data
            return {
                "expired_cheques": cheques,
                "expired_guarantors": guarantors,
                "expired_trade_license": result_set.get("expired_trade_license"),
                "expired_attachment": result_set.get("expired_attachment"),
            }
        return {}

    def update(self, instance, validated_data):
        if instance.stage == "" or validated_data.get("stage") == "":
            instance.stage = None
            validated_data["stage"] = None
        return super().update(instance, validated_data)

    class Meta:
        model = Party
        fields = "__all__"


class PartyTrailSerializer(ModelSerializer):
    dealing = DealingSerializer(read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)

    def to_representation(self, instance: Party):
        response = super().to_representation(instance)

        serialized_keys: Dict[str, Serializer] = {
            "division": DivisionSerializer(instance=instance.division),
            "district": DistrictSerializer(instance=instance.district),
            "party_category": PartyCategorySerializer(instance=instance.party_category),
            "police_station": PoliceStationserializer(instance=instance.police_station),
            "sales_person": UserSerializer(instance=instance.sales_person),
            "created_by": UserSerializer(instance=instance.created_by),
            "updated_by": UserSerializer(instance=instance.updated_by),
        }
        for key, value in serialized_keys.items():
            response[key] = value.data

        return response

    class Meta:
        model = Party
        fields = "__all__"
