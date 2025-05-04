from rest_framework import serializers

from ..models.tender import Ministry, Participant, Team, TenderType


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "team_name"]


class MinistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ministry
        fields = ["id", "ministry_name"]


class TenderTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderType
        fields = ["id", "type_name"]


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = "__all__"
