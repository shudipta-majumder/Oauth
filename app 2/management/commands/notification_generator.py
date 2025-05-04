from datetime import timedelta
from logging import getLogger

from django.core.management.base import BaseCommand
from django.db.models import Max, Q
from django.utils import timezone

from ...models.contract_agreement import ContractAgreement
from ...models.noa import NotificationOfAward
from ...models.tender import Tender
from ...utils import create_update_notification, delete_notification

logger = getLogger(__name__)


class Command(BaseCommand):
    help = "Check Tender, Notification of award and contract agreement tables and create/update Notification entries"

    def manage_pg_validity_notification(self, tender):
        # If pg_released_status is True, delete all notifications for this tender
        if tender:
            delete_notification(tender=tender, notification_type="PG")
        # Check for the latest PG Released Date
        latest_pg_released_date = tender.pg_released_date.aggregate(Max("date"))[
            "date__max"
        ]
        if latest_pg_released_date:
            deadline = latest_pg_released_date
        else:
            # If no PG Released Date, check the pg_validity_date in NOA
            noa = NotificationOfAward.objects.filter(tender=tender).first()
            if noa and noa.pg_validity_date:
                deadline = noa.pg_validity_date
            else:
                deadline = None
        if deadline:
            # Calculate remaining time
            remaining_time = (deadline - timezone.now().date()).days
            # Create or update the notification
            if 0 <= remaining_time <= 7:
                create_update_notification(
                    tender=tender,
                    notification_type="PG",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )

    def manage_bg_validity_notification(self, tender):
        # If bg_released_status is True, delete the notification
        if tender:
            delete_notification(tender=tender, notification_type="BG")
        # Check for the latest BG Released Date
        latest_bg_released_date = tender.bg_released_date.aggregate(Max("date"))[
            "date__max"
        ]

        if latest_bg_released_date:
            deadline = latest_bg_released_date
        else:
            # If no BG Released Date, check the latest BG Validity Date
            latest_bg_validity_date = tender.bg_valid_dates.aggregate(
                Max("bg_valid_date")
            )["bg_valid_date__max"]
            deadline = latest_bg_validity_date

        if deadline:
            # Calculate remaining time
            remaining_time = deadline - timezone.now().date()

            # Create or update the notification
            if 0 <= remaining_time.days <= 7:
                create_update_notification(
                    tender=tender,
                    notification_type="BG",
                    deadline=deadline,
                    remaining_time=remaining_time.days,
                )

    def handle(self, *args, **kwargs):
        # Get all tenders that have a bg_validity_date
        tenders = Tender.objects.filter(
            bg_released_status__isnull=True
        ) | Tender.objects.filter(bg_released_status=False)
        for tender in tenders:
            self.manage_bg_validity_notification(tender)

        tenders = Tender.objects.filter(
            Q(pg_released_status__isnull=True) | Q(pg_released_status=False)
        )
        for tender in tenders:
            self.manage_pg_validity_notification(tender)

        # Create notification for NOA ACCEPTANCE DEADLINE
        noa_list = NotificationOfAward.objects.filter(
            noa_acceptance_deadline__isnull=False
        )
        for noa in noa_list:
            if noa.noa_acceptance_deadline:
                remaining_time = noa.noa_acceptance_deadline - timezone.now().date()
                if 0 <= remaining_time.days <= 7:
                    delete_notification(
                        tender=noa.tender, notification_type="NOA ACCEPTANCE DEADLINE"
                    )
                    create_update_notification(
                        tender=noa.tender,
                        notification_type="NOA ACCEPTANCE DEADLINE",
                        deadline=noa.noa_acceptance_deadline,
                        remaining_time=remaining_time.days,
                    )
                if remaining_time.days < 0:
                    # Delete notification if remaining time is negative
                    delete_notification(
                        tender=noa.tender, notification_type="NOA ACCEPTANCE DEADLINE"
                    )

        # Create a contract agreement notification for tenders that don't have the contract agreement attachment.
        tender_instances = Tender.objects.filter(
            noa__contract_agreement_deadline__isnull=False,
            contract_agreement__contract_agreement_attch__isnull=True,
        )
        for instance in tender_instances:
            deadline = instance.noa.contract_agreement_deadline
            remaining_time = deadline - timezone.now().date()

            # Create or update the notification
            if 0 <= remaining_time.days <= 10:
                delete_notification(
                    tender=instance, notification_type="CONTRACT AGREEMENT DEADLINE"
                )
                create_update_notification(
                    tender=instance,
                    notification_type="CONTRACT AGREEMENT DEADLINE",
                    remaining_time=remaining_time.days,
                    deadline=deadline,
                )
        # Create a DELIVERY DEADLINE notification for tenders that have the delivery_deadline but is_tender_complete field is No.
        contract_agreement_instances = ContractAgreement.objects.filter(
            delivery_deadline__isnull=False
        ).exclude(is_tender_complete="Yes")
        for instance in contract_agreement_instances:
            deadline = instance.delivery_deadline
            total_duration = deadline - instance.contract_agreement_date
            # Calculate 60% of the total duration in seconds
            total_duration_seconds = total_duration.total_seconds()
            threshold_duration_seconds = total_duration_seconds * 0.6
            threshold_duration = timedelta(seconds=threshold_duration_seconds)

            # Calculate the threshold date (60% of the way)
            threshold_date = instance.contract_agreement_date + threshold_duration
            # Create or update the notification
            if timezone.now().date() >= threshold_date:
                remaining_time = (deadline - timezone.now().date()).days
                create_update_notification(
                    tender=instance.tender,
                    notification_type="DELIVERY DEADLINE",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )
