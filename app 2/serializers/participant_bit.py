from rest_framework import serializers

from ..models.participant_bids import ParticipantBid


class ParticipantBidsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipantBid
        fields = "__all__"
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Add separate fields for participant_id and participant_name
        if instance.participant_name:
            representation['participant_id'] = instance.participant_name.id
            representation['participant_name'] = instance.participant_name.name

        return representation