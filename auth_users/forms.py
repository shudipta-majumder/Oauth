from django.contrib.auth.forms import UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "full_name",
            "designation",
            "mobile",
            "is_management",
            "is_active",
            "recommended",
        )
