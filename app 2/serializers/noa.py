from datetime import datetime
from logging import getLogger

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from ..models.noa import BGReleasedDate, NotificationOfAward
from ..utils import create_update_notification, delete_notification, process_attachment

logger = getLogger(__name__)


class BGReleasedDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BGReleasedDate
        fields = "__all__"

    def save(self, **kwargs):
        instance = self.instance
        if instance is None:
            instance = super().save(**kwargs)
        else:
            instance = super().save(**kwargs)

        # Perform the business logic for BGReleasedDate
        if instance.is_bg_released == "Yes":
            logger.info(
                f"BG released for Tender {instance.tender.id}. Updating status."
            )
            delete_notification(tender=instance.tender, notification_type="BG")
            instance.tender.bg_released_status = True
            instance.tender.save()
        if instance.date and instance.is_bg_released != "Yes":
            delete_notification(tender=instance.tender, notification_type="BG")
            if isinstance(instance.date, str):
                deadline = datetime.strptime(instance.date, "%Y-%m-%d").date()
            else:
                deadline = instance.date

            remaining_time = deadline - timezone.now().date()
            if 0 <= remaining_time.days <= 7:
                # Create a new notification
                create_update_notification(
                    tender=instance.tender,
                    notification_type="BG",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )

        logger.info(f"BGReleasedDate saved for Tender {instance.tender.id}.")
        return instance


class NoaSerializer(serializers.ModelSerializer):
    bg_released_date = BGReleasedDateSerializer(many=True, required=False)

    class Meta:
        model = NotificationOfAward
        fields = "__all__"

    @transaction.atomic
    def create(self, validated_data):
        bg_released_dates = validated_data.pop("bg_released_date", [])
        tender = validated_data.get("tender")
        # Create the NotificationOfAward instance
        noa_instance = NotificationOfAward.objects.create(**validated_data)

        # Create associated BGReleasedDate instances
        for bg_released_date in bg_released_dates:
            tender = bg_released_date.pop("tender")
            bg_released_date["tender"] = tender.id
            serializer = BGReleasedDateSerializer(data=bg_released_date)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
        # BGReleasedDate.objects.create(tender=tender, **bg_released_date)
        if noa_instance.noa_status == "No":
            noa_instance.tender.is_open = False
            noa_instance.tender.save()

        if noa_instance.pg_validity_date:
            delete_notification(tender=noa_instance.tender, notification_type="PG")

            if isinstance(noa_instance.pg_validity_date, str):
                deadline = datetime.strptime(
                    noa_instance.pg_validity_date, "%Y-%m-%d"
                ).date()
            else:
                deadline = noa_instance.pg_validity_date

            remaining_time = deadline - timezone.now().date()

            if 0 <= remaining_time.days <= 7:
                # Create a new notification
                create_update_notification(
                    tender=noa_instance.tender,
                    notification_type="PG",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )
        if noa_instance.noa_acceptance_deadline:
            delete_notification(
                tender=noa_instance.tender, notification_type="NOA ACCEPTANCE DEADLINE"
            )
            if isinstance(noa_instance.noa_acceptance_deadline, str):
                deadline = datetime.strptime(
                    noa_instance.noa_acceptance_deadline, "%Y-%m-%d"
                ).date()
            else:
                deadline = noa_instance.noa_acceptance_deadline

            remaining_time = deadline - timezone.now().date()

            if 0 <= remaining_time.days <= 7:
                # Create a new notification
                create_update_notification(
                    tender=noa_instance.tender,
                    notification_type="NOA ACCEPTANCE DEADLINE",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )
        if noa_instance.contract_agreement_deadline:
            delete_notification(
                tender=noa_instance.tender,
                notification_type="CONTRACT AGREEMENT DEADLINE",
            )
            if isinstance(noa_instance.contract_agreement_deadline, str):
                deadline = datetime.strptime(
                    noa_instance.contract_agreement_deadline, "%Y-%m-%d"
                ).date()
            else:
                deadline = noa_instance.contract_agreement_deadline

            remaining_time = deadline - timezone.now().date()

            if 0 <= remaining_time.days <= 10:
                # Create a new notification
                create_update_notification(
                    tender=noa_instance.tender,
                    notification_type="CONTRACT AGREEMENT DEADLINE",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )

        return noa_instance

    @transaction.atomic
    def update(self, instance, validated_data):
        bg_released_dates = validated_data.pop("bg_released_date", [])
        tender = instance.tender.id
        BGReleasedDate.objects.filter(tender=tender).delete()
        for bg_released_date in bg_released_dates:
            bg_released_date["tender"] = tender
            serializer = BGReleasedDateSerializer(data=bg_released_date)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
        instance = super().update(instance, validated_data)
        if instance.noa_status == "No":
            instance.tender.is_open = False
            instance.tender.save()
        if instance.pg_validity_date:
            delete_notification(tender=instance.tender, notification_type="PG")
            if isinstance(instance.pg_validity_date, str):
                deadline = datetime.strptime(
                    instance.pg_validity_date, "%Y-%m-%d"
                ).date()
            else:
                deadline = instance.pg_validity_date

            remaining_time = deadline - timezone.now().date()

            if 0 <= remaining_time.days <= 7:
                # Create a new notification
                create_update_notification(
                    tender=instance.tender,
                    notification_type="PG",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )

        if instance.noa_acceptance_deadline:
            delete_notification(
                tender=instance.tender, notification_type="NOA ACCEPTANCE DEADLINE"
            )
            if isinstance(instance.noa_acceptance_deadline, str):
                deadline = datetime.strptime(
                    instance.noa_acceptance_deadline, "%Y-%m-%d"
                ).date()
            else:
                deadline = instance.noa_acceptance_deadline

            remaining_time = deadline - timezone.now().date()

            if 0 <= remaining_time.days <= 7:
                # Create a new notification
                create_update_notification(
                    tender=instance.tender,
                    notification_type="NOA ACCEPTANCE DEADLINE",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )

        if instance.contract_agreement_deadline:
            delete_notification(
                tender=instance.tender,
                notification_type="CONTRACT AGREEMENT DEADLINE",
            )
            if isinstance(instance.contract_agreement_deadline, str):
                deadline = datetime.strptime(
                    instance.contract_agreement_deadline, "%Y-%m-%d"
                ).date()
            else:
                deadline = instance.contract_agreement_deadline

            remaining_time = deadline - timezone.now().date()

            if 0 <= remaining_time.days <= 10:
                # Create a new notification
                create_update_notification(
                    tender=instance.tender,
                    notification_type="CONTRACT AGREEMENT DEADLINE",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        domain = ""
        if request:
            domain = request.build_absolute_uri("/")
            if domain.endswith("/"):
                domain = domain[:-1]

        representation["noa_attachment"] = process_attachment(
            instance.noa_attachment, domain
        )

        representation["pg_attachment"] = process_attachment(
            instance.pg_attachment, domain
        )
        representation["bg_released_date"] = BGReleasedDateSerializer(
            instance.tender.bg_released_date.all(), many=True
        ).data

        return representation
