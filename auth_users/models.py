from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.mixins import AuditLogMixin
from core.validators import PhoneNumberValidator

from .managers import (
    CustomUserManager,
)


class Role(AuditLogMixin):
    codename = models.CharField(max_length=255, unique=True, verbose_name="Code Name")
    viewname = models.CharField(max_length=255, verbose_name="View Name", db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "oss_user_roles"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return str(self.viewname)


class User(AbstractUser, AuditLogMixin):
    username_validator = UnicodeUsernameValidator()
    phone_validator = PhoneNumberValidator()

    class YesNoChoice(models.TextChoices):
        YES = "yes", _("Yes")
        NO = "no", _("No")
        NA = "n/a", _("Not Applicable")

    username = models.CharField(
        _("User ID"),
        max_length=55,
        unique=True,
        help_text=_(
            "Required. 55 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that userid already exists."),
        },
    )
    full_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Name",
    )
    designation = models.CharField(
        max_length=150,
        null=True,
        blank=True,
    )
    phone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        validators=[phone_validator],
    )
    supervisor_id = models.CharField(max_length=20, null=True, blank=True)
    supervisor_name = models.CharField(max_length=20, null=True, blank=True)
    hod_id = models.CharField(max_length=20, null=True, blank=True)
    hod_name = models.CharField(max_length=20, null=True, blank=True)
    is_management = models.BooleanField(
        _("management"),
        default=False,
        help_text=_(
            "Designates whether this use should be treated as management. "
            "Unselect this instead of deleting accounts."
        ),
    )

    recommended = models.CharField(
        _("Recommended"),
        default=YesNoChoice.NA,
        choices=YesNoChoice.choices,
        max_length=10,
    )

    roles = models.ManyToManyField(Role)

    otp_code = models.CharField(null=True, blank=True, editable=False, max_length=10)
    otp_timestamp = models.DateTimeField(null=True, blank=True, editable=False)

    objects = CustomUserManager()

    def __str__(self) -> str:
        return f"{str(self.username)} - {self.full_name}"

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["password"]

    class Meta:
        permissions = (
            ("can_recommend_salesperson", "Can Recommend Sales Person"),
            ("has_pms_access", "Has PMS access"),
            ("has_cpq_access", "Has CPQ access"),
        )
