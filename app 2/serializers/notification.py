from rest_framework import serializers

from ..models.notification import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Extracting only the days from the remaining_time duration
        if instance.remaining_time:
            representation["remaining_time"] = instance.remaining_time.days
        else:
            representation["remaining_time"] = 0

        return representation
