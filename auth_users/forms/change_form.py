from django.contrib.auth.forms import UserChangeForm
from django.forms import CheckboxSelectMultiple

from ..models import User

__all__ = ["CustomUserChangeForm"]


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
        widgets = {"roles": CheckboxSelectMultiple}
