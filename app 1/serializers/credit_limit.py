from rest_framework import serializers as sz

from auth_users.serializers import UserSerializer
from recommendation_engine.serializers import ApprovalQueueSerializer

from ..models import CreditLimit, CreditLimitDetail, EbsCollectionDetail

__all__ = [
    "CreditLimitSerializer",
    "CreditLimitDetailSerializer",
    "CreditLimitDetailMSerializer",
    "EbsCollectionDetailSerializer",
]


class CreditLimitSerializer(sz.ModelSerializer):
    approval_queues = ApprovalQueueSerializer(many=True, read_only=True)

    class Meta:
        model = CreditLimit
        fields = "__all__"

    def to_representation(self, instance: CreditLimit):
        representation = super().to_representation(instance)
        request = self.context.get("request")
        if request:
            # Get the URI for the attachment field without the domain
            if instance.wo_po_mou:
                url = instance.wo_po_mou.url
                domain = request.build_absolute_uri("/")[:-1]
                representation["wo_po_mou"] = url.replace(domain, "")
            if instance.rating_certificate:
                url = instance.wo_po_mou.url
                domain = request.build_absolute_uri("/")[:-1]
                representation["rating_certificate"] = url.replace(domain, "")
            if instance.updated_ledger_wdc:
                url = instance.updated_ledger_wdc.url
                domain = request.build_absolute_uri("/")[:-1]
                representation["updated_ledger_wdc"] = url.replace(domain, "")
            if instance.updated_ledger_wcl:
                url = instance.updated_ledger_wcl.url
                domain = request.build_absolute_uri("/")[:-1]
                representation["updated_ledger_wcl"] = url.replace(domain, "")

        representation["limit_details"] = CreditLimitDetailSerializer(
            instance.creditlimitdetail_set.all(), many=True
        ).data
        representation["collections"] = EbsCollectionDetailSerializer(
            instance.collection_details.all(), many=True
        ).data
        representation["created_by"] = UserSerializer(instance=instance.created_by).data
        representation["updated_by"] = UserSerializer(instance=instance.updated_by).data
        return representation


class CreditLimitDetailMSerializer(sz.ModelSerializer):
    class Meta:
        model = CreditLimitDetail
        fields = "__all__"


class CreditLimitDetailSerializer(sz.ModelSerializer):
    class Meta:
        model = CreditLimitDetail
        fields = "__all__"

    def to_representation(self, instance: CreditLimitDetail):
        response = super().to_representation(instance)
        request = self.context.get("request")
        if request:
            # Get the URI for the attachment field without the domain
            if instance.micr_cheque:
                url = instance.micr_cheque.url
                domain = request.build_absolute_uri("/")[:-1]
                response["micr_cheque"] = url.replace(domain, "")
        return response


class EbsCollectionDetailSerializer(sz.ModelSerializer):
    class Meta:
        model = EbsCollectionDetail
        fields = "__all__"
