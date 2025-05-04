from drf_writable_nested.mixins import UniqueFieldsMixin
from rest_framework.serializers import (
    ModelSerializer,
)

from core.constants import EXCLUDE_FIELDS

from ..models import BankIssuerLov, BranchIssuerBankLov

__all__ = [
    "BankIssuerSerializer",
    "BranchIssuerSerializer",
]


class BankIssuerSerializer(UniqueFieldsMixin, ModelSerializer):
    class Meta:
        model = BankIssuerLov
        exclude = EXCLUDE_FIELDS


class BranchIssuerSerializer(UniqueFieldsMixin, ModelSerializer):
    class Meta:
        model = BranchIssuerBankLov
        exclude = EXCLUDE_FIELDS
