import logging

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger(__name__)


@shared_task(name="notification_generator", bind=True, retry_kwargs={"max_retries": 10})
def generate_notification(self):
    call_command("notification_generator")
