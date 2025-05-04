import secrets
import string
from datetime import timedelta
from logging import getLogger

import httpx  # noqa: F401
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from oauth2_provider.models import AccessToken, Application, IDToken
from oauthlib.common import generate_token
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response

from core.openapi_metadata import OpenApiTags
from core.permissions import HasRecommendPermission, IsOwnerAccountOrAdminPermission
from core.renderer import CustomRenderer

from . import models, serializers, task

logging = getLogger("auth_users.views")

OTP_VALIDITY_MINUTES = 10


class HRMSLoginException(exceptions.APIException):
    ...


def generate_reset_pwd_email(
    otp: int | str, user: models.User, otp_expires_in: int
) -> str:
    """helper function to generate an formatted html email with given OTP"""
    context = {"otp": otp, "user": user, "otp_expires_in": otp_expires_in}
    email_html = render_to_string("auth_users/reset_password_email.html", context)
    return email_html


def generate_reset_pwd_success_email(user: models.User) -> str:
    context = {"full_name": user.full_name, "email": user.email}
    email_html = render_to_string("auth_users/reset_password_completed.html", context)
    return email_html


def generate_otp(length: int = 6) -> str:
    """helper function to generate random OTP with digit"""
    characters = string.digits
    otp = "".join(secrets.choice(characters) for _ in range(length))
    return otp


def generate_password(length: int = 8) -> str:
    """helper function to generate random password"""
    characters = string.ascii_letters + string.digits
    password = "".join(secrets.choice(characters) for _ in range(length))
    return password


@extend_schema(tags=[OpenApiTags.Users])
class UserViewSet(viewsets.ViewSet):
    queryset = models.User.objects.all().order_by("-created_at")
    serializer_class = serializers.UserSerializer
    required_scopes = ["read"]

    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    renderer_classes = (CustomRenderer,)

    def get_permissions(self):
        if self.action in (
            "destroy",
            "update",
            "partial_update",
        ):
            self.permission_classes = [IsAdminUser, IsAuthenticatedOrTokenHasScope]

        if self.action in (
            "retrieve",
            "me",
        ):
            self.permission_classes = [
                IsOwnerAccountOrAdminPermission,
                IsAuthenticatedOrTokenHasScope,
            ]

        if self.action in (
            "approve_salesman_account",
            "pending_approvals",
        ):
            self.permission_classes = [
                IsAuthenticatedOrTokenHasScope,
                HasRecommendPermission,
            ]

        return [permission() for permission in self.permission_classes]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "salesman",
                OpenApiTypes.BOOL,
                required=False,
            )
        ],
        responses={200: serializers.UserSerializer(many=True)},
        description="Fetch All Users. Can be filtered also with different types of "
        "params.",
        summary="Get all Users in the system",
    )
    def list(self, request: Request):
        self.check_permissions(request)
        salesman_flag = request.query_params.get("salesman")

        if salesman_flag == "true":
            self.queryset = self.queryset.filter(
                groups__isnull=True,
                is_management=False,
                is_staff=False,
                is_superuser=False,
            )

        serialized_users = serializers.UserSerializer(instance=self.queryset, many=True)

        return Response(serialized_users.data)

    @extend_schema(
        responses={
            200: serializers.UserSerializer,
        },
        summary="Get single user with ID",
        description="Fetch a single user from system with given ID.",
    )
    def retrieve(self, request: Request, pk: int):
        try:
            user = models.User.objects.get(pk=pk)
        except models.User.DoesNotExist as err:
            logging.error(f"User with id {pk!r} not found: {str(err)!r}")
            raise exceptions.NotFound(err.args, status.HTTP_404_NOT_FOUND) from err
        try:
            self.check_object_permissions(request, user)
        except exceptions.PermissionDenied as err:
            logging.warning(f"Permission denied: {str(err)!r}")
            raise exceptions.PermissionDenied(
                err.get_full_details(), err.status_code
            ) from err
        serialized_user = serializers.UserSerializer(instance=user)
        logging.info(f"Retrieved user with id {pk!r}")

        return Response(serialized_user.data)

    @extend_schema(
        responses={200: serializers.UserSerializer},
        summary="Get current logged-in user details",
        description="Fetch the current authenticated user details from system.",
    )
    @action(methods=["get"], detail=False)
    def me(self, request: Request):
        """Fetch the current logged-in users profile information"""
        user = models.User.objects.get(username=request.user.username)
        serialized_user = serializers.UserSerializer(instance=user)

        return Response(serialized_user.data)

    @extend_schema(
        request={"application/json": serializers.UserSerializer},
        responses={200: serializers.UserSerializer},
        summary="Update a user instance",
        description="Update a user instance in system. All the fields (mandatory) are required.",
    )
    def update(self, request: Request, pk: int):
        try:
            existing_user = models.User.objects.get(pk=pk)
        except models.User.DoesNotExist as err:
            logging.error(f"User with id {pk!r} not found: {str(err)!r}")
            raise exceptions.NotFound(err.args, status.HTTP_404_NOT_FOUND) from err
        serialized_user = serializers.UserSerializer(
            instance=existing_user, data=request.data
        )

        if serialized_user.is_valid():
            serialized_user.save()
            userout_schema = serializers.UserSerializer(
                instance=serialized_user.instance
            )
            logging.info(f"User with id {pk!r} updated successfully")
            return Response(userout_schema.data, status.HTTP_200_OK)
        logging.error(
            f"Validation error while updating user with id {pk!r}: {str(serialized_user.errors)!r}"
        )
        raise exceptions.ValidationError(
            serialized_user.errors, status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        request={"application/json": serializers.UserSerializer},
        responses={
            200: serializers.UserSerializer,
        },
        summary="Partially update a user instance",
        description="Partially update a user instance in system. Only given fields are updated.",
    )
    def partial_update(self, request: Request, pk: int):
        try:
            existing_user = models.User.objects.get(pk=pk)
        except models.User.DoesNotExist as err:
            logging.error(f"User with id {pk!r} not found: {str(err)!r}")
            raise exceptions.NotFound(err.args, status.HTTP_404_NOT_FOUND) from err
        serialized_user = serializers.UserSerializer(
            instance=existing_user, data=request.data, partial=True
        )

        try:
            serialized_user.is_valid(raise_exception=True)
        except exceptions.ValidationError as err:
            logging.error(
                f"Validation error while updating user with id {pk!r}: {str(serialized_user.errors)!r}"
            )
            raise exceptions.ValidationError(
                serialized_user.errors, status.HTTP_400_BAD_REQUEST
            ) from err

        serialized_user.save()
        logging.info(f"User with id {pk!r} updated successfully")
        return Response(serialized_user.data, status.HTTP_200_OK)

    @extend_schema(
        summary="Remove a user",
        description="Remove a user from the system. User ID is required.",
    )
    def destroy(self, request: Request, pk: int):
        try:
            user = models.User.objects.get(pk=pk)
        except models.User.DoesNotExist as err:
            logging.error(f"User with id {pk!r} not found: {str(err)!r}")
            raise exceptions.NotFound(err.args, status.HTTP_404_NOT_FOUND) from err

        user.delete()
        logging.info(f"User with id {pk!r} deleted successfully")
        return Response(None, status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={
            200: serializers.OkResponse,
        },
        request=serializers.ChangePwdSerializer,
        summary="Change Password for me",
    )
    @action(methods=["post"], detail=False, url_path="change-pwd")
    def change_password(self, request: Request) -> Response:
        """
        1. **Endpoint**:
           - The endpoint for changing the password is `POST /change-pwd`.

        2. **Request Format**:
           - The front-end needs to send a POST request to the above endpoint.
           - The request body should be a JSON object containing `"current_pwd"` and `"new_pwd"` fields.
           - `"current_pwd"` should represent the user's current password.
           - `"new_pwd"` should represent the new password the user wants to set.

        3. **Response Handling**:
           - The API returns different HTTP status codes for different scenarios:
             - `HTTP 204 NO CONTENT` if the password change is successful.
             - `HTTP 400 BAD REQUEST` if there are validation errors in the input data (e.g., new password not meeting criteria).
             - `HTTP 401 UNAUTHORIZED` if the provided current password doesn't match the user's actual current password.

        4. **Validation Errors**:
           - If the front-end receives a `HTTP 400 BAD REQUEST`, it means there are validation errors in the request data.
           - The API response will contain detailed error messages indicating what criteria the new password failed to meet (e.g., length, character requirements).

        5. **Error Handling**:
           - Handle `HTTP 401 UNAUTHORIZED` by informing the user that their provided current password is incorrect.
           - For `HTTP 400 BAD REQUEST`, display the specific validation errors to guide users on the password requirements.

        6. **Security and Policy**:
           - The API enforces specific password policies:
             - Minimum length requirement.
             - Presence of uppercase and lowercase characters, digits, and special characters.
           - Ensure the front-end communicates these policy requirements to users when they attempt to change their password.

        7. **UX Considerations**:
           - Provide clear and user-friendly error messages when the password change fails due to validation or authentication issues.
           - Guide users about the password policy requirements to help them create a password that meets the criteria.

        8. **Form Handling**:
           - Use proper form validation on the front-end to ensure the user enters both the current and new passwords correctly before making the API call.
           - Consider client-side validation to provide immediate feedback about password policy adherence before sending the request to the API.
        """
        current_user = request.user

        payload = serializers.ChangePwdSerializer(data=request.data)

        if not payload.is_valid():
            logging.error(
                f"Validation error while changing password for user {str(current_user)!r}: {str(payload.errors)!r}"
            )
            raise exceptions.ValidationError(
                payload.errors, status.HTTP_400_BAD_REQUEST
            )

        if not current_user.check_password(payload.validated_data.get("current_pwd")):
            logging.warning(
                f"Password change failed for user {str(current_user)!r}: current password mismatch"
            )
            raise exceptions.NotAcceptable(
                "password mismatch", status.HTTP_401_UNAUTHORIZED
            )

        current_user.set_password(payload.validated_data.get("new_pwd"))
        current_user.save()
        logging.info(f"Password changed successfully for user {str(current_user)!r}")
        return Response("ok")

    @extend_schema(
        summary="Fetch salesman users waiting for approval",
        request=None,
        responses={
            200: serializers.UserSerializer(many=True),
        },
    )
    @action(methods=["get"], detail=False, url_path="pending-approvals")
    def pending_approvals(self, request: Request):
        """List of salesman accounts that requires approval. User needs a `Recommender` role to access this route."""
        users = models.User.objects.filter(
            recommended=models.User.YesNoChoice.NO
        ).order_by("-created_at")
        serialized_users = serializers.UserSerializer(instance=users, many=True)
        return Response(serialized_users.data)

    @extend_schema(
        summary="Approve a salesman account by stakeholder",
        request=None,
        responses={200: serializers.OkResponse},
    )
    @action(methods=["post"], detail=True, url_path="approve")
    def approve_salesman_account(self, request: Request, pk: int):
        """
        1. **Endpoint**:
           - The endpoint is used to approve a salesman's account.
           - URL Pattern: `/api/v1/auth/users/{id}/approve/`
           - Method: `POST`

        2. **Request**:
           - The front-end needs to send a `POST` request to this endpoint.
           - It expects a valid `pk` (primary key) of the salesman account to be approved.

        3. **Response Handling**:
           - The API returns an HTTP status code:
             - `HTTP 200 OK` if the account approval is successful.
             - `HTTP 404 NOT FOUND` if the provided `pk` doesn't correspond to any salesman account.

        4. **Account Approval**:
           - Upon a successful request, the salesman's account with the given `pk` will be updated to be active (`is_active = True`).
           - The `updated_by` field in the `Salesman` model is updated with the current user who triggered the approval (using `request.user`).

        5. **Success Response**:
           - The API response for a successful approval returns an `HTTP 200 OK` status code with a simple message `"ok"` indicating successful approval.

        6. **Error Handling**:
           - If the provided `pk` does not correspond to any salesman account, the API returns an `HTTP 404 NOT FOUND` status along with an error message indicating the absence of the user.

        7. **Security Considerations**:
           - Ensure proper authentication and authorization to access this endpoint.
           - Only authorized users with appropriate permissions should be able to approve salesman accounts.
        """
        try:
            salesman = models.User.objects.get(pk=pk)
            if salesman.recommended:
                raise exceptions.NotAcceptable(
                    "Already Recommended", status.HTTP_400_BAD_REQUEST
                )
        except models.User.DoesNotExist as err:
            logging.error(f"Salesman with id {pk!r} not found: {str(err)!r}")
            raise exceptions.NotFound(err.args) from err
        else:
            salesman.is_active = True
            salesman.recommended = models.User.YesNoChoice.YES
            salesman.updated_by = request.user
            salesman.save()
            logging.info(f"Salesman account with id {pk!r} approved successfully")
            return Response("ok")


@extend_schema_view(
    register=extend_schema(
        request={"application/json": serializers.UserInSerializer},
        responses={
            201: serializers.UserSerializer,
        },
        description="Request to create an Salesman Account. Authentic Employee ID is required for "
        "Opening an account. Also an approval will be sent to concern Department. User "
        "won't be able to login util account is approved.",
        summary="Create New account for Salesman",
    ),
    forgot_password=extend_schema(
        request=None,
        responses={200: serializers.ForgotPwdOutSerializer},
        parameters=[OpenApiParameter("id", OpenApiTypes.STR, OpenApiParameter.PATH)],
        description="Request to change the password if forgotten. An email will be send to user authorized mail.",
        summary="Forgot Password",
    ),
    forgot_password_callback=extend_schema(
        request={"application/json": serializers.ForgotPwdCallbackSerializer},
        responses={200: serializers.ForgotPwdCallbackOutSerializer},
        description="OTP Verify after user has requested an OTP. `username` and `otp` need to provide in body.",
        summary="OTP Verifier Callback URL",
    ),
)
@extend_schema(tags=[OpenApiTags.Accounts])
class AccountViewSet(viewsets.ViewSet):
    """ViewSet only responsible for Salesman account registration purpose. Other types of user should be created
    from django admin panel only.
    """

    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (CustomRenderer,)

    @extend_schema(
        request={"application/json": serializers.LoginSerializer},
        summary="Login User with HRMS ID & Password",
        description="A verification of HRMS and process will be handled with HRMS user id",
    )
    @action(methods=["post"], detail=False)
    def login(self, request: Request):
        serialized_data = serializers.LoginSerializer(data=request.data)

        if not serialized_data.is_valid():
            raise exceptions.ValidationError(
                "Username, Password fields are required !", status.HTTP_400_BAD_REQUEST
            )
        try:
            current_user = models.User.objects.get(
                username=serialized_data.data.get("username")
            )
        except models.User.DoesNotExist as err:
            logging.error(
                f"User with username {serialized_data.data.get('username')!r} not found: {str(err)!r}"
            )
            raise exceptions.NotFound(err.args) from err

        if not settings.DEBUG:
            response = httpx.post(
                f"{settings.HRMS_API_ENDPOINT}/generateToken", json=serialized_data.data
            )

            if response.status_code != status.HTTP_200_OK:
                raise HRMSLoginException(
                    detail=response.json(), code=response.status_code
                )

            current_user.set_password(serialized_data.data.get("password"))
            current_user.save()

        application = Application.objects.get(client_id=settings.PMS_NEXTJS_CLIENT_ID)

        id_token = IDToken.objects.create(
            user=current_user,
            application=application,
            expires=timezone.now() + timedelta(days=3 * 10),
        )
        access_token = AccessToken.objects.create(
            user=current_user,
            id_token=id_token,
            token=generate_token(length=64),
            application=application,
            scope="read write openid introspection",
            expires=timezone.now() + timedelta(days=3 * 10),
        )
        serialized_user = serializers.UserSerializer(instance=current_user)
        logging.info(f"User {current_user!r} logged in successfully")
        return Response({"token": access_token.token, **serialized_user.data})

    @action(methods=["post"], detail=False)
    def register(self, request: Request):
        serialized_data = serializers.UserInSerializer(data=request.data)

        try:
            serialized_data.is_valid(raise_exception=True)
        except exceptions.ValidationError as err:
            logging.error(f"Validation error during user registration: {str(err)!r}")
            raise exceptions.ValidationError(
                err.get_full_details(), status.HTTP_400_BAD_REQUEST
            ) from err
        else:
            salesman = models.User(**serialized_data.validated_data)
            salesman.password = salesman.set_password(salesman.password)
            salesman.is_management = False
            salesman.is_active = False
            salesman.is_staff = False
            salesman.is_superuser = False
            salesman.recommended = models.User.YesNoChoice.NO
            salesman.save()
            logging.info(f"New salesman registered: {str(salesman)!r}")
            return Response(serialized_data.data, status.HTTP_201_CREATED)

    @action(methods=["post"], detail=True, url_path="resetpwd")
    def forgot_password(self, request: Request, pk: str):
        try:
            user = models.User.objects.get(username=pk)
            if not user.email:
                raise exceptions.ValidationError(
                    f"{user.username!r} doesn't have any email.",
                    status.HTTP_400_BAD_REQUEST,
                )

            otp = generate_otp()
            email_content = generate_reset_pwd_email(
                otp=otp, user=user, otp_expires_in=OTP_VALIDITY_MINUTES
            )
        except models.User.DoesNotExist as err:
            logging.error(f"User with username {pk!r} not found: {str(err)!r}")
            raise exceptions.NotFound(err.args, status.HTTP_404_NOT_FOUND) from err

        user.otp_code = otp
        user.otp_timestamp = timezone.now()
        user.save()
        out_response = serializers.ForgotPwdOut(
            username=user.username,
            otp_generated_time=user.otp_timestamp,
            otp_validity_minutes=OTP_VALIDITY_MINUTES,
        )
        logging.info(f"OTP generated for user {user.username!r}")
        # long running task, delegating responsibility to celery task queue
        task.send_email.delay(user.email, "PMS: Reset Password", email_content)
        logging.info(f"Reset password email sent to {user.email!r}")
        return Response(out_response.as_dict())

    @action(methods=["post"], detail=False, url_path="resetpwd-callback")
    def forgot_password_callback(self, request: Request):
        data = request.data

        if not data.get("username", None) or not data.get("otp", None):
            raise exceptions.ValidationError(
                "username and otp are required fields", status.HTTP_400_BAD_REQUEST
            )

        username = data.get("username")

        try:
            user = models.User.objects.get(username=username)
        except models.User.DoesNotExist as err:
            logging.error(f"User with username {username!r} not found: {str(err)!r}")
            raise exceptions.NotFound(err.args, status.HTTP_404_NOT_FOUND) from err

        if not user.email:
            logging.error(f"User {username!r} doesn't have any email.")
            raise exceptions.ValidationError(
                f"{user.username!r} doesn't have any email.",
                status.HTTP_400_BAD_REQUEST,
            )

        if user.otp_code != data.get("otp"):
            logging.error("Invalid OTP code received.")
            raise exceptions.ValidationError(
                "invalid otp code", status.HTTP_406_NOT_ACCEPTABLE
            )

        if (
            not (user.otp_timestamp + timedelta(minutes=OTP_VALIDITY_MINUTES))
            > timezone.now()
        ):
            logging.error("OTP code expired.")
            return Response("otp code expired", status.HTTP_406_NOT_ACCEPTABLE)

        random_pwd = generate_password()
        user.set_password(random_pwd)
        user.otp_code = None
        user.otp_timestamp = None
        user.save()
        email_content = generate_reset_pwd_success_email(user)
        out_response = serializers.ForgotPwdCallbackOut(
            username=user.username, temporary_password=random_pwd
        )
        # long-running process, delegating the process to celery
        task.send_email(
            user.email, "PMS: Did you just reset your password?", email_content
        )
        logging.info(
            f"Password reset successfully for user {username!r}. New temporary password sent to {user.email !r}"
        )
        return Response(out_response.as_dict())
