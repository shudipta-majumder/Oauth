from rest_framework import serializers

from ..models.tender import TenderSubmissionTimeStamps


class TenderSubmissionTimeStampsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderSubmissionTimeStamps
        fields = "__all__"
