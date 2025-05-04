import json
from logging import getLogger

from rest_framework.exceptions import ValidationError

from .models.notification import Notification

logger = getLogger(__name__)


def parse_json_data(data, data_name):
    if isinstance(data, str):
        try:
            parsed_data = json.loads(data)
            if not isinstance(parsed_data, list):
                raise ValidationError(f"{data_name} should be a list of dictionaries")
        except json.JSONDecodeError:
            raise ValidationError(f"{data_name} is not a valid JSON")  # noqa: B904
        return parsed_data
    return data


def create_update_notification(tender, notification_type, deadline, remaining_time):
    """
    Create or update notification for a tender.
    """
    Notification.objects.update_or_create(
        tender=tender,
        notification_type=notification_type,
        defaults={
            "tender_id_ref": tender.tender_id,
            "team_name": tender.team_name if tender.team_name else None,
            "tender_type": tender.tender_type if tender.tender_type else None,
            "procurring_entity": tender.procuring_entity
            if tender.procuring_entity
            else None,
            "kam_name": tender.kam_name if tender.kam_name else None,
            "deadline": deadline if deadline else None,
            "remaining_time": remaining_time if remaining_time else None,
        },
    )
    logger.info(
        f"{notification_type} notification created/updated for Tender ID: {tender.tender_id} with {remaining_time} days remaining."
    )


def delete_notification(tender, notification_type):
    """
    Delete all notifications of a specific type for a tender.
    """
    Notification.objects.filter(
        tender=tender, notification_type=notification_type
    ).delete()
    logger.info(
        f"Deleted all notifications of type {notification_type} for Tender ID: {tender.tender_id}"
    )


def process_attachment(field_value, domain):
    """
    Process the attachment URL by removing the domain part.

    Args:
        field_value: The field value containing the URL.
        domain: The domain to be removed from the URL.

    Returns:
        The processed URL with the domain removed, or None if field_value is None.
    """
    if field_value:
        return field_value.url.replace(domain, "")
    return None
