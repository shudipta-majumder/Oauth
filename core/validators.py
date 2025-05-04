from django.core import validators
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class PhoneNumberValidator(validators.RegexValidator):
    regex = r"^(\+8801|8801|01|008801)[1|3-9]{1}(\d){8}$"

    message = _(
        "Enter a valid phone number. This value may contain only digits from 0-9, "
        "valid phone numbers are that starts with +880 or 880, 0088 or just the "
        "number like 01778000002"
    )
    flags = 0
