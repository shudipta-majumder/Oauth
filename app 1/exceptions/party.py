from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status

__all__ = ["PartyNotFoundException"]


class PartyNotFoundException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Party does not exists.")
    default_code = "party_error"
