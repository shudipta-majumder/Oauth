from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from oauth2_provider.models import AccessToken
from rest_framework import status

from auth_users.models import User
from auth_users.services.hrms_service import HRMSService


@receiver(post_save, sender=User)
def fillup_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        service = HRMSService()
        api_status, response = service.get_employee_detail(instance.username)
        if api_status == status.HTTP_200_OK:
            instance.email = response.get("email", None)
            instance.full_name = response.get("displayName", None)
            instance.phone = response.get("phone", None)
            instance.designation = response.get("designation", None)
            instance.save()


@receiver(post_save, sender=AccessToken, dispatch_uid="record_last_login")
def record_login(sender, instance, created, **kwargs):
    if created:
        instance.user.last_login = timezone.now()
        instance.user.save()
