import uuid
from datetime import datetime, timedelta
from logging import getLogger

from django.db import models
from django.utils import timezone

from core.mixins import AuditLogMixin

from ..utils import create_update_notification, delete_notification
from .noa import NotificationOfAward
from .tender import Tender

logger = getLogger(__name__)


class ContractAgreement(models.Model):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    contract_agreement_attch = models.FileField(
        upload_to="contracts/", null=True, blank=True
    )
    contract_agreement_date = models.DateField(null=True, blank=True)
    delivery_deadline_input_days = models.CharField(
        max_length=100, null=True, blank=True
    )
    delivery_deadline = models.DateField(null=True, blank=True)
    traning_installation = models.CharField(max_length=100, null=True, blank=True)
    delivery_start_date = models.DateField(null=True, blank=True)
    delivery_complition_date = models.DateField(null=True, blank=True)
    is_tender_complete = models.CharField(max_length=100, null=True, blank=True)
    completion_certificate = models.FileField(
        upload_to="certificates/", null=True, blank=True
    )
    noa = models.OneToOneField(NotificationOfAward, on_delete=models.CASCADE)
    tender = models.OneToOneField(
        Tender, on_delete=models.CASCADE, related_name="contract_agreement"
    )

    def __str__(self):
        return f"{self.id}"

    def save(self, *args, **kwargs):
        logger.info("Starting save method for ContractAgreement with ID %s", self.id)
        if self.is_tender_complete == "Yes" and not self.completion_certificate:
            logger.info(
                "Tender is complete but no completion certificate provided for tender ID %s",
                self.tender.id,
            )
            # Create or update the notification
            create_update_notification(
                tender=self.tender,
                notification_type="COMPLETION CERTIFICATE",
                deadline=timezone.now().date(),
                remaining_time=0,
            )
            logger.info("Completion certificate notification created or updated.")
        # If the completion certificate is provided, delete the notification
        if self.is_tender_complete == "Yes" and self.completion_certificate:
            logger.info(
                "Tender is complete and completion certificate provided for tender ID %s",
                self.tender.id,
            )
            delete_notification(
                tender=self.tender, notification_type="COMPLETION CERTIFICATE"
            )
        if self.contract_agreement_attch:
            delete_notification(
                tender=self.tender, notification_type="CONTRACT AGREEMENT DEADLINE"
            )
        if (
            self.delivery_deadline
            and self.contract_agreement_date
            and not self.is_tender_complete
        ):
            if isinstance(self.contract_agreement_date, str):
                agreement_date = datetime.strptime(
                    self.contract_agreement_date, "%Y-%m-%d"
                ).date()
            else:
                agreement_date = self.contract_agreement_date

            if isinstance(self.delivery_deadline, str):
                deadline = datetime.strptime(self.delivery_deadline, "%Y-%m-%d").date()
            else:
                deadline = self.delivery_deadline
            total_duration = deadline - agreement_date
            # Calculate 60% of the total duration in seconds
            total_duration_seconds = total_duration.total_seconds()
            threshold_duration_seconds = total_duration_seconds * 0.6
            threshold_duration = timedelta(seconds=threshold_duration_seconds)
            # Calculate the threshold date (60% of the way)
            threshold_date = agreement_date + threshold_duration
            if timezone.now().date() >= threshold_date:
                remaining_time = deadline - timezone.now().date()
                delete_notification(
                    tender=self.tender, notification_type="DELIVERY DEADLINE"
                )
                # Create a new notification
                create_update_notification(
                    tender=self.tender,
                    notification_type="DELIVERY DEADLINE",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )
            else:
                delete_notification(
                    tender=self.tender, notification_type="DELIVERY DEADLINE"
                )
        if self.is_tender_complete == "Yes":
            self.tender.is_open = False
            self.tender.save()
            delete_notification(
                tender=self.tender, notification_type="DELIVERY DEADLINE"
            )

        super().save(*args, **kwargs)
        logger.info("Save method completed for ContractAgreement with ID %s", self.id)


class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    vendor_attachment = models.FileField(upload_to="vendor/", null=True, blank=True)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="vendor")
    # contract = models.ForeignKey(ContractAgreement, on_delete=models.CASCADE, related_name="vendor")

    def __str__(self):
        return self.vendor_name


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_amount = models.CharField(max_length=255, null=True, blank=True)
    payment_attachment = models.FileField(upload_to="payments/", null=True, blank=True)
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="payment")

    def __str__(self):
        return (
            str(self.payment_amount) if self.payment_amount is not None else "No Amount"
        )


class PGReleasedDate(AuditLogMixin):
    date = models.DateField(null=True, blank=True)
    is_pg_released = models.CharField(max_length=100, null=True, blank=True)
    tender = models.ForeignKey(
        Tender, on_delete=models.CASCADE, related_name="pg_released_date"
    )

    def save(self, *args, **kwargs):
        if self.is_pg_released == "Yes":
            logger.info(f"PG released for Tender {self.tender.id}. Updating status.")
            delete_notification(tender=self.tender, notification_type="PG")
            self.tender.pg_released_status = True
            self.tender.save()
        if self.date and self.is_pg_released != "Yes":
            if isinstance(self.date, str):
                deadline = datetime.strptime(self.date, "%Y-%m-%d").date()
            else:
                deadline = self.date
            remaining_time = deadline - timezone.now().date()
            if 0 <= remaining_time.days <= 7:
                delete_notification(tender=self.tender, notification_type="PG")
                # Create a new notification
                create_update_notification(
                    tender=self.tender,
                    notification_type="PG",
                    deadline=deadline,
                    remaining_time=remaining_time,
                )
            else:
                delete_notification(tender=self.tender, notification_type="PG")
        super().save(*args, **kwargs)
        logger.info(f"PGReleasedDate saved for Tender {self.tender.id}.")
