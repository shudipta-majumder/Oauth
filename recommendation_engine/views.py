from logging import getLogger

from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.constants import StatusChoices
from core.renderer import CustomRenderer

from .models import ApprovalQueue, ApprovalStep, RecommendationProcess
from .serializers import (
    ApprovalQueueSerializer,
    ApprovalStepSerializer,
    ApprovalUpdateSerializer,
)

__all__ = ["RecommendationDecisionView", "ApprovalStepViewSet"]

logging = getLogger("recommendation_engine.views")


class AlreadyApprovedException(exceptions.APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = _("Object is already approved.")
    default_code = "queue_error"


class PermissionDeniedException(exceptions.APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("Role not authorized to approve.")
    default_code = "permission_denied"


class UnknownException(exceptions.APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Unknown Error"
    default_code = "unknown_error"


class RecommendationDecisionView(APIView):
    serializer_class = ApprovalQueueSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def get_queryset(self):
        return ApprovalQueue.objects.all()

    @extend_schema(request=ApprovalUpdateSerializer)
    def patch(self, request: Request, pk: int):
        current_user = request.user
        role: Group = current_user.groups.first()
        queue = ApprovalQueue.objects.get(pk=pk)

        if role.name.upper() != queue.node.approval_step.codename.upper():
            raise PermissionDeniedException("Role does not match approval step.")

        if queue.status == StatusChoices.APPROVED:
            raise AlreadyApprovedException()

        chains = ApprovalQueue.objects.filter(object_id=queue.object_id).order_by(
            "node__approval_step__forward_step"
        )

        for chain in chains:
            if chain.node.approval_step.codename == queue.node.approval_step.codename:
                break
            if chain.status != StatusChoices.APPROVED:
                raise PermissionDeniedException("Role does not match approval step.")

        serialized_data = ApprovalUpdateSerializer(
            instance=queue, data=request.data, partial=True
        )

        if not serialized_data.is_valid():
            raise exceptions.ValidationError(serialized_data.errors)

        serialized_data.save()

        return Response(self.serializer_class(queue).data)


class ApprovalStepViewSet(APIView):
    serializer_class = ApprovalStepSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def get_queryset(self):
        return ApprovalStep.objects.all()

    @extend_schema(request=ApprovalStepSerializer)
    def get(self, request: Request, process: str):
        try:
            process = RecommendationProcess.objects.get(codename=process)
            qs = self.get_queryset().filter(process=process).order_by("forward_step")
            return Response(self.serializer_class(qs, many=True).data)
        except Exception as exc:
            logging.exception(exc)
            raise UnknownException(str(exc)) from exc
