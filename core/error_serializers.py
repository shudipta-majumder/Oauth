from django.db import models
from rest_framework import serializers, status


class StatusChoices(models.IntegerChoices):
    HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
    HTTP_200_OK = status.HTTP_200_OK
    HTTP_202_ACCEPTED = status.HTTP_202_ACCEPTED
    HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    HTTP_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    HTTP_403_FORBIDDEN = status.HTTP_403_FORBIDDEN
    HTTP_401_UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    HTTP_204_NO_CONTENT = status.HTTP_204_NO_CONTENT


class BaseSerializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=StatusChoices.choices)
    message = serializers.CharField()
    errors = serializers.ListField(default=[])
    data = serializers.ListField(default=[])


class Http400ValidationErrorResponse(BaseSerializer):
    code = serializers.ChoiceField(
        choices=StatusChoices.choices, default=StatusChoices.HTTP_400_BAD_REQUEST
    )
    message = serializers.CharField(default="Validation Error")
    errors = serializers.ListField(
        default=[{"errorFieldName": ["validation field error details"]}]
    )


class Http401NotAuthorizedResponse(BaseSerializer):
    code = serializers.ChoiceField(
        choices=StatusChoices.choices, default=StatusChoices.HTTP_401_UNAUTHORIZED
    )
    message = serializers.CharField(default="Unauthorized")
    errors = serializers.ListField(
        default=[
            {"message": "unauthorized error details", "code": "authorization_error"}
        ]
    )


class Http403ForbiddenResponse(BaseSerializer):
    code = serializers.ChoiceField(
        choices=StatusChoices.choices, default=StatusChoices.HTTP_403_FORBIDDEN
    )
    message = serializers.CharField(default="Forbidden")
    errors = serializers.ListField(
        default=[{"message": "forbidden error details", "code": "permission_denied"}]
    )


class Http404NotFoundResponse(BaseSerializer):
    code = serializers.ChoiceField(
        choices=StatusChoices.choices, default=StatusChoices.HTTP_404_NOT_FOUND
    )
    message = serializers.CharField(default="Not Found")
    errors = serializers.ListField(default=[{"message": "object not found detail"}])


class Http500ServerErrorResponse(BaseSerializer):
    code = serializers.ChoiceField(
        choices=StatusChoices.choices,
        default=StatusChoices.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    message = serializers.CharField(default="Server Error")
    errors = serializers.ListField(default=["server error details"])
