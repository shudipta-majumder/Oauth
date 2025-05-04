import uuid
from logging import getLogger

from django.db import models
from django.db.models import CASCADE

from core.mixins import AuditLogMixin

logger = getLogger(__name__)


# This Team model is a setup table for Tender this tabel will suggest several team name during the creation of Tender instance.
class Team(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    team_name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self) -> str:
        return self.team_name


# This Ministry model is a setup table for Tender this tabel will suggest several Ministry name during the creation of Tender instance.
class Ministry(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    ministry_name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self) -> str:
        return self.ministry_name


# This TenderType model is a setup table for Tender this tabel will suggest several Tender Type during the creation of Tender instance.
class TenderType(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    type_name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self) -> str:
        return self.type_name


# This Tender model is the main model of this project.
class Tender(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    tender_id = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        verbose_name="Tender ID/Ref",
        unique=True,
    )
    is_open = models.BooleanField(default=True)
    team_name = models.ForeignKey(Team, max_length=255, on_delete=CASCADE)
    kam_name = models.CharField(max_length=255)
    tender_type = models.ForeignKey(TenderType, max_length=255, on_delete=CASCADE)
    tender_description = models.TextField()
    procuring_entity = models.CharField(max_length=255, null=True, blank=True)
    ministry = models.ForeignKey(
        Ministry, max_length=255, null=True, blank=True, on_delete=CASCADE
    )
    bg_amount = models.CharField(null=True, blank=True, max_length=100)
    bg_attachment = models.FileField(upload_to="tenders/", null=True, blank=True)
    bg_issue_date = models.DateField(null=True, blank=True)
    tender_budget_lower_per = models.CharField(null=True, blank=True, max_length=100)
    tender_budget_lower = models.CharField(null=True, blank=True, max_length=100)
    tender_budget_upper_per = models.CharField(null=True, blank=True, max_length=100)
    tender_budget_upper = models.CharField(null=True, blank=True, max_length=100)
    pretender_meeting_date = models.DateTimeField(null=True, blank=True)
    attend_pre_tender_meeting = models.BooleanField(null=True, blank=True)
    pretender_meeting_attachment = models.FileField(
        upload_to="pretender_meeting_attachments/", blank=True, null=True
    )
    has_external_application = models.BooleanField(null=True, blank=True)
    external_application_attach = models.FileField(
        upload_to="external_application_attachments/", blank=True, null=True
    )
    is_tender_submitted = models.CharField(null=True, blank=True, max_length=100)
    technical_compliance_sheet = models.FileField(
        upload_to="technical_compliance_sheet/", blank=True, null=True
    )
    result = models.CharField(max_length=100, null=True, blank=True)
    biding_price_type = models.CharField(max_length=100, null=True, blank=True)
    biding_price_national = models.CharField(null=True, blank=True, max_length=100)
    biding_price_international = models.CharField(null=True, blank=True, max_length=100)
    reason = models.CharField(max_length=255, null=True, blank=True)
    analytics_note = models.TextField(max_length=255, null=True, blank=True)
    bg_released_status = models.BooleanField(null=True, blank=True)
    pg_released_status = models.BooleanField(null=True, blank=True)
    probable_cost_breakdown_one = models.TextField(max_length=255, null=True, blank=True)
    probable_cost_breakdown_two = models.TextField(max_length=255, null=True, blank=True)
    is_bi_analysis_done = models.BooleanField(null=True, blank=True)
    # setper = models.CharField(default=1, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.tender_id}"

    def save(self, *args, **kwargs):
        # To aviod circular import I have to import it here
        from .notification import Notification

        if self.is_tender_submitted == "No":
            self.is_open = False
        if self.bg_released_status:
            # Delete all notifications of type "BG" related to this tender
            Notification.objects.filter(tender=self, notification_type="BG").delete()
            logger.info(f"Delete all Notification of BG Of tender : {self.tender_id}")
        if self.pg_released_status:
            # Delete all notifications of type "BG" related to this tender
            Notification.objects.filter(tender=self, notification_type="PG").delete()
            logger.info(f"Delete all Notification of BG Of tender : {self.tender_id}")

        super().save(*args, **kwargs)


# This table store the bank guarentee extention data as well as its validity date.
class BGValidityDate(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    bg_valid_date = models.DateField(null=True, blank=True)
    tender = models.ForeignKey(
        Tender, max_length=255, on_delete=CASCADE, related_name="bg_valid_dates"
    )

    def __str__(self) -> str:
        return f"{self.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


#  This table store the time stamp of submission.
class TenderSubmissionTimeStamps(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_date = models.DateTimeField(null=True, blank=True)
    # submission_time = models.TimeField()
    tender = models.ForeignKey(
        Tender, on_delete=CASCADE, related_name="tender_submission_timestamp"
    )

    def __str__(self):
        return f"submission_date={self.submission_date}"


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Participant Name"
    )

    def __str__(self) -> str:
        return self.name
