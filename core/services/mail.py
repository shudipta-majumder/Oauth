from dataclasses import dataclass
from email.message import EmailMessage
from logging import getLogger
from smtplib import SMTP

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException

logging = getLogger("core.services.mail")


class MailServerError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "ohoo! something wrong with email server. please try later."
    default_code = "mailserver_error"


@dataclass
class Email:
    receiver: str
    subject: str
    body: str
    is_html: bool = True
    sender: str = settings.MAIL_SENDER_ADDR

    def __post_init__(self):
        if not self.receiver:
            raise ValueError("Receiver is required")

    def get_content(self) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = self.subject
        msg["From"] = self.sender
        msg["To"] = self.receiver

        if self.is_html:
            msg.set_content(self.body, subtype="html")
        else:
            msg.set_content(self.body)
        return msg


class Mail:
    @classmethod
    def send(cls, email: Email):
        try:
            with SMTP(host=settings.SMTP_HOST, port=settings.SMTP_PORT) as mail_server:
                mail_server.starttls()
                mail_server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                mail_server.send_message(email.get_content())
                logging.info(f"an email has been sent for email={email.receiver!r}")
                return {"status": "ok"}
        except Exception as e:
            logging.exception(e.args)
            raise MailServerError(
                detail=" // ".join(str(arg) for arg in e.args), code=500
            ) from e
