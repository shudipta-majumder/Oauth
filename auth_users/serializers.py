import re
from dataclasses import dataclass
from datetime import datetime

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    group = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        read_only_fields = (
            "pk",
            "full_name",
            "designation",
            "phone",
            "last_login",
        )
        exclude = (
            "groups",
            "user_permissions",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "first_name",
            "last_name",
            "password",
        )

    def get_group(self, obj: User) -> str | None:
        group = obj.groups.first()
        if group:
            return group.name.upper()
        return None


class UserInSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = (
            "id",
            "groups",
            "user_permissions",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
            "first_name",
            "last_name",
            "last_login",
            "is_superuser",
            "date_joined",
            "is_staff",
            "is_active",
            "is_management",
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class LoginOutSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    current_user = UserSerializer()


class ChangePwdSerializer(serializers.Serializer):
    current_pwd = serializers.CharField(required=True)
    new_pwd = serializers.CharField(required=True)

    def validate_new_pwd(self, value):
        min_length = 8
        has_uppercase = any(char.isupper() for char in value)
        has_lowercase = any(char.islower() for char in value)
        has_digit = any(char.isdigit() for char in value)
        has_special = bool(re.search(r"[^a-zA-Z0-9\s]", value))

        if len(value) < min_length:
            raise serializers.ValidationError(
                f"password must be at-least {min_length} characters long"
            )

        if not has_uppercase or not has_lowercase:
            raise serializers.ValidationError(
                "password must contain at-least 1 uppercase and lowercase character"
            )

        if not has_digit:
            raise serializers.ValidationError("password must contain at-least 1 digit")

        if not has_special:
            raise serializers.ValidationError(
                "password must contain at-least 1 special character like (@, !, &, *, %, #, ?)"
            )

        return value

    def validate(self, attrs):
        if "current_pwd" in attrs and "new_pwd" in attrs:
            if attrs["current_pwd"] == attrs["new_pwd"]:
                raise serializers.ValidationError(
                    "New password should be different from the current password."
                )

        return attrs


class ForgotPwdCallbackSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    otp = serializers.IntegerField(required=True)


@dataclass
class ForgotPwdOut:
    username: str
    otp_generated_time: datetime
    otp_validity_minutes: int

    def as_dict(self):
        return {
            "username": self.username,
            "otp_generated_time": self.otp_generated_time,
            "otp_validity_minutes": self.otp_validity_minutes,
        }


class ForgotPwdOutSerializer(serializers.Serializer):
    username = serializers.CharField()
    otp_generated_time = serializers.DateTimeField()
    otp_validity_minutes = serializers.IntegerField()


@dataclass
class ForgotPwdCallbackOut:
    username: str
    temporary_password: str

    def as_dict(self):
        return {
            "username": self.username,
            "temporary_password": self.temporary_password,
        }


class ForgotPwdCallbackOutSerializer(serializers.Serializer):
    username = serializers.CharField()
    temporary_password = serializers.CharField()


class ValidationErrorResponse(serializers.Serializer):
    code = serializers.IntegerField()
    msg = serializers.CharField(max_length=20)
    errors = serializers.ListField(allow_null=True, allow_empty=True)
    data = serializers.DictField()


class OkResponse(serializers.Serializer):
    code = serializers.IntegerField(default=202)
    msg = serializers.CharField(default="Accepted")
    errors = serializers.ListField(default=[])
    data = serializers.CharField(default="ok")


class FailureResponse(serializers.Serializer):
    code = serializers.IntegerField(default=404)
    msg = serializers.CharField(default="Error")
    errors = serializers.ListField(default=["user not found with pk"])
    data = serializers.CharField(allow_null=True, allow_blank=True, default=None)
