from logging import getLogger

from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.openapi_metadata.metadata import OpenApiTags
from core.pagination import StandardResultSetPagination
from core.renderer import CustomRenderer
from pms.models.party import Party

from ..models import AttachmentRepository, ExtraAttachment, PartyAttachment
from ..serializers import (
    AttachmentRepositorySerializer,
    AttachmentSerializer,
    ExtraSerializer,
)

logging = getLogger("pms.views.attachment")


__all__ = ["AttachmentViewSet", "AttachmentRepoViewSet", "ExtraAttachmentViewSet"]


class AttachmentFoundException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Attachment item does not exists.")
    default_code = "attachment_error"


@extend_schema(tags=[OpenApiTags.ATTACHMENTS])
class AttachmentViewSet(ModelViewSet):
    queryset = PartyAttachment.objects.all()
    serializer_class = AttachmentSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    pagination_class = StandardResultSetPagination
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def delete_file(self, instance, field_name):
        file_field = getattr(instance, field_name)
        if file_field:
            file_field.delete(save=False)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="step",
                type=OpenApiTypes.NUMBER,
                location=OpenApiParameter.QUERY,
                required=False,
            )
        ]
    )
    def create(self, request: Request) -> Response:
        remarks = request.data.pop("remarks", None)

        serialized_data = self.serializer_class(data=request.data)

        if not serialized_data.is_valid():
            logging.error(
                f"Validation error at attachment create method: {str(serialized_data.errors)!r}"
            )
            raise exceptions.ValidationError(serialized_data.errors)

        serialized_data.save()

        if remarks:
            party = serialized_data.instance.party
            party.remarks = remarks[-1]
            party.save()

        query_param = request.query_params.get("step", None)

        if query_param:
            party = Party.objects.get(id=serialized_data.instance.party.id)
            party.stepper_index = query_param
            party.save()
        logging.info("Attachment created successfully.")
        return Response(serialized_data.data, status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="step",
                type=OpenApiTypes.NUMBER,
                location=OpenApiParameter.QUERY,
                required=False,
            )
        ]
    )
    def partial_update(self, request: Request, pk: int) -> Response:
        """Update a attachment info partially"""
        query_param = request.query_params.get("step", None)
        remarks = request.data.pop("remarks", None)

        try:
            dealing = PartyAttachment.objects.get(id=pk)
        except PartyAttachment.DoesNotExist as e:
            logging.error(f"PartyAttachment with id {pk!r} does not exist.")
            raise AttachmentFoundException from e
        payload = self.serializer_class(
            instance=dealing, data=request.data, partial=True
        )

        if not payload.is_valid():
            logging.error(
                f"Validation error at attachment partial update : {str(payload.errors)!r}"
            )
            raise exceptions.ValidationError(payload.errors)
        payload.save()

        party = payload.instance.party

        for field_name in payload.validated_data.keys():
            if field_name.endswith("_desc") or field_name == "party":
                continue  # Skip non-file fields
            if field_name in request.data and request.data[field_name] is None:
                # Delete the file associated with the field
                self.delete_file(payload.instance, field_name)

        if remarks:
            party.remarks = remarks[-1]

        if query_param:
            # Side Effect as hardcore frontend doesn't have the ablity to call API.
            party.stepper_index = query_param
        party.save()

        serialized_dealing = self.serializer_class(instance=dealing)
        logging.info(f"PartyAttachment with id {pk!r} partially updated.")
        return Response(serialized_dealing.data)

    def destroy(self, request: Request, pk: int) -> Response:
        obj = PartyAttachment.objects.get(pk=pk)
        obj.delete()
        return Response(None, status=status.HTTP_200_OK)


class AttachmentRepoFilter(filters.FilterSet):
    class Meta:
        model = AttachmentRepository
        fields = ("is_active", "parent_id")


@extend_schema(tags=[OpenApiTags.ATTACHMENTS])
class AttachmentRepoViewSet(ModelViewSet):
    queryset = AttachmentRepository.objects.all().order_by("codename")
    serializer_class = AttachmentRepositorySerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    pagination_class = None
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = AttachmentRepoFilter

    def destroy(self, request: Request, pk: int) -> Response:
        obj = AttachmentRepository.objects.get(pk=pk)
        obj.delete()
        return Response(None, status=status.HTTP_200_OK)


@extend_schema(tags=[OpenApiTags.EXTRA_ATTACHMENT])
class ExtraAttachmentViewSet(ModelViewSet):
    queryset = ExtraAttachment.objects.all()
    serializer_class = ExtraSerializer
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    pagination_class = None
    required_scopes = ["read"]
    renderer_classes = (CustomRenderer,)

    def destroy(self, request: Request, pk: int) -> Response:
        obj = ExtraAttachment.objects.get(pk=pk)
        obj.delete()
        return Response(None, status=status.HTTP_200_OK)
