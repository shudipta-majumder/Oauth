from datetime import datetime
from logging import getLogger

from django.utils import timezone
from rest_framework import serializers

from ..models.tender import BGValidityDate
from ..utils import create_update_notification, delete_notification

logger = getLogger(__name__)


class BGValidityDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BGValidityDate
        fields = "__all__"

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        if instance.bg_valid_date:
            if isinstance(instance.bg_valid_date, str):
                deadline = datetime.strptime(instance.bg_valid_date, "%Y-%m-%d").date()
            else:
                deadline = instance.bg_valid_date

            remaining_time = deadline - timezone.now().date()

            if 0 <= remaining_time.days <= 7:
                delete_notification(tender=instance.tender, notification_type="BG")

                # Create a new notification
                create_update_notification(
                    tender=instance.tender,
                    notification_type="BG",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )
            else:
                delete_notification(tender=instance.tender, notification_type="BG")

        return instance
