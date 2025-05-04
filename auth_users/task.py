from celery import shared_task

from core.services.mail import Email
from core.services.mail import Mail as MailService


@shared_task
def send_email(receiver: str, subject: str, body: str, is_html: bool = True):
    email = Email(receiver=receiver, subject=subject, body=body, is_html=is_html)
    return MailService.send(email)
