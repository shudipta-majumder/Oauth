from datetime import datetime, timedelta
from logging import getLogger
from uuid import UUID

import oracledb
from celery import shared_task
from django.conf import settings

from core.constants import StatusChoices
from pms.models.credit_limit import CreditLimit
from pms.services.credit_limit_services import CreditLimitService

from .signals import generate_approval_chain

_logger = getLogger(__name__)


@shared_task(
    name="Credit Limit Post Process", bind=True, retry_kwargs={"max_retries": 10}
)
def run_credit_limit_post_process(self, crl_id: UUID):
    try:
        crl = CreditLimit.objects.get(id=crl_id)
        with oracledb.connect(params=settings.EBS_CONN_PARAMS) as connection:
            row = CreditLimitService.get_party_grading(crl.witp_code, connection)
            max_due_count = CreditLimitService.get_max_inv_due_count(
                crl.witp_code, connection
            )
            party_status = CreditLimitService().get_party_status(
                crl.witp_code, connection=connection
            )
            default_addr = CreditLimitService.get_party_default_addr(
                crl.witp_code, connection
            )
            collections = CreditLimitService().get_party_collections(
                crl.witp_code, connection
            )

            CreditLimitService.create_party_collections(crl, collections)
            CreditLimitService.set_credit_limit_extra_details(
                crl, row.grade, max_due_count, party_status, default_addr
            )

            generate_approval_chain(crl, row=row)
    except (oracledb.DatabaseError, Exception) as exc:
        raise self.retry(exc=exc, countdown=2)  # noqa: B904


@shared_task(name="credit_limit_cleanup", bind=True, retry_kwargs={"max_retries": 10})
def credit_limit_cleanup(self):
    try:
        date_of_earlier_three_day = datetime.now() - timedelta(days=3)
        # Filter and delete CreditLimit objects that are in INIT status and older than three days
        deleted_count, _ = CreditLimit.objects.filter(
            status=StatusChoices.INIT, created_at__lt=date_of_earlier_three_day
        ).delete()
        if deleted_count:
            return {
                "status": f"Removed {deleted_count} stale credit limit applications."
            }
        return {"status": "No Stale Credit Limit Application Found."}
    except Exception as exc:
        _logger.exception(exc)
        self.retry(exc=exc, countdown=2)
