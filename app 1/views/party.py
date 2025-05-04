import uuid
from datetime import datetime, timedelta
from http import HTTPMethod
from logging import getLogger

from django.contrib.auth.models import Group
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)
from rest_framework import exceptions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from auth_users.models import User
from core.constants import StatusChoices
from core.openapi_metadata.metadata import OpenApiTags
from core.pagination import StandardResultSetPagination
from core.renderer import CustomRenderer
from pms.constants import PMSRecommendationStages

from ..exceptions import PartyNotFoundException
from ..models import Party, PartyDealing
from ..serializers import PartySerializer, WITPSerializer

logger = getLogger("pms.views.party")

__all__ = [
    "PartyViewSet",
]


class ServerError(exceptions.APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Internal Server Error"
    default_code = "server_error"


def is_incharge(role: Group) -> bool:
    if not role:
        return False
    return role.name.lower() == PMSRecommendationStages.INCHARGE.value.lower()


def is_ebs_team(role: Group) -> bool:
    target_role_name = PMSRecommendationStages.EBS_TEAM.value.lower()
    return role.name.lower() == target_role_name


@extend_schema(tags=[OpenApiTags.PARTY])
class PartyViewSet(ViewSet):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    queryset = Party.objects.filter(~Q(status=StatusChoices.ARCHIVED)).order_by(
        "-created_at"
    )
    serializer_class = PartySerializer
    pagination_class = StandardResultSetPagination
    required_scopes = ["read"]
    renderer_classes = [
        CustomRenderer,
    ]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "q",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                "status",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                enum=StatusChoices,
            ),
            OpenApiParameter(
                "start_date",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                required=False,
                description="Format: YYYY-MM-DD",
            ),
            OpenApiParameter(
                "end_date",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                required=False,
                description="Format: YYYY-MM-DD",
            ),
        ]
    )
    def list(self, request: Request) -> Response:  # noqa: C901
        """Get all the parties. Response will be paginated."""
        current_user: User = request.user
        role: Group = current_user.groups.first()

        if current_user.is_management:
            self.queryset = self.queryset.filter(~Q(status=StatusChoices.DRAFT))
        else:
            self.queryset = self.queryset.filter(created_by=current_user)

        has_status = request.query_params.get("status", "").strip()
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)
        query = request.query_params.get("q", None)

        if query != '""' and query != "''" and query:
            self.queryset = self.queryset.filter(
                Q(id__iexact=query)
                | Q(witp_code__iexact=query)
                | Q(party_name__icontains=query)
                | Q(owner_name__icontains=query)
            )

        if has_status and has_status != "" and has_status != "all":
            # TODO: need to use match case for below conditions
            if has_status == StatusChoices.PENDING:
                if not role:
                    self.queryset = self.queryset.filter(
                        status=StatusChoices.PENDING
                    ).order_by("-created_at")
                else:
                    self.queryset = self.queryset.filter(
                        status=StatusChoices.PENDING,
                        stage__iexact=role.name,
                        approval_queues__status=StatusChoices.PENDING,
                        approval_queues__node__user=current_user,
                    ).distinct()
            if has_status == StatusChoices.APPROVED:
                if not role:
                    self.queryset = self.queryset.filter(
                        status=StatusChoices.APPROVED
                    ).order_by("-created_at")
                else:
                    self.queryset = self.queryset.filter(
                        (
                            Q(status=StatusChoices.APPROVED)
                            & Q(stage=StatusChoices.APPROVED)
                        )
                        | (
                            Q(status=StatusChoices.PENDING)
                            & Q(approval_queues__status=StatusChoices.APPROVED)
                            & Q(approval_queues__node__user=current_user)
                        )
                    ).distinct()
            if has_status == StatusChoices.REJECTED:
                self.queryset = self.queryset.filter(
                    status=StatusChoices.REJECTED
                ).order_by("-created_at")
            if has_status == StatusChoices.DRAFT:
                self.queryset = self.queryset.filter(
                    Q(status=StatusChoices.DRAFT) & ~Q(process="existing_party")
                ).order_by("-created_at")
        else:
            if role:
                self.queryset = self.queryset.filter(
                    Q(stage__in=[StatusChoices.APPROVED, StatusChoices.REJECTED])
                    | (
                        Q(stage__iexact=role.name)
                        & Q(approval_queues__status=StatusChoices.PENDING)
                        & Q(approval_queues__node__user=current_user)
                    )
                    | (
                        Q(status=StatusChoices.PENDING)
                        & Q(approval_queues__status=StatusChoices.APPROVED)
                        & Q(approval_queues__node__user=current_user)
                    )
                ).distinct()
            else:
                self.queryset = self.queryset.filter(next_node__isnull=True)

        try:
            if start_date and end_date:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(
                    days=1
                )
                self.queryset = self.queryset.filter(
                    created_at__range=(start_datetime, end_datetime)
                )

        except ValueError as exc:
            logger.error("could not parse the given dates in url params")
            logger.exception(exc)

        paginator = self.pagination_class()
        paginator.set_page_size(request)
        paginated_queryset = paginator.paginate_queryset(
            self.queryset.prefetch_related("dealing", "contacts", "attachments"),
            request,
        )
        serialized_data = self.serializer_class(instance=paginated_queryset, many=True)
        return paginator.get_paginated_response(serialized_data.data)

    def retrieve(self, request: Request, pk: uuid.UUID) -> Response:
        """Retrieve a single party"""
        try:
            party = Party.objects.get(id=pk)
        except Party.DoesNotExist as e:
            logger.error(f"Party with id {pk!r} does not exist.")
            raise PartyNotFoundException from e

        serialized_party = self.serializer_class(instance=party)
        logger.info(f"Retrieved party ID {pk!r}.")
        return Response(serialized_party.data)

    @extend_schema(request=PartySerializer)
    def create(self, request: Request) -> Response:
        """Create new Party"""
        serialized_data = PartySerializer(data=request.data)
        if not serialized_data.is_valid():
            raise exceptions.ValidationError(serialized_data.error_messages)

        serialized_data.validated_data["created_by"] = request.user
        serialized_data.save()
        PartyDealing.objects.create(party=serialized_data.instance)
        return Response(serialized_data.data, status.HTTP_201_CREATED)

    @extend_schema(request=PartySerializer)
    def partial_update(self, request: Request, pk: uuid.UUID) -> Response:
        """Update a party partially"""
        try:
            party = Party.objects.get(id=pk)
        except Party.DoesNotExist as exc:
            logger.error(f"Party with id {pk!r} does not exist.")
            raise PartyNotFoundException() from exc

        serialized_data = PartySerializer(
            instance=party, data=request.data, partial=True
        )
        if not serialized_data.is_valid():
            raise exceptions.ValidationError(serialized_data.error_messages)

        serialized_data.validated_data["updated_by"] = request.user
        serialized_data.save()
        return Response(serialized_data.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
            )
        ]
    )
    @action(methods=[HTTPMethod.GET], detail=True, url_path="byWitp")
    def by_witp(self, request: Request, pk: str) -> Response:
        """Search party by witp code."""
        try:
            party = Party.objects.get(
                witp_code=pk,
                status=StatusChoices.APPROVED,
                stage=StatusChoices.APPROVED,
            )
        except Party.DoesNotExist as e:
            logger.error(f"Party with id {pk!r} does not exist.")
            raise PartyNotFoundException from e
        serialized_party = self.serializer_class(instance=party)

        return Response(serialized_party.data)

    @extend_schema(
        request=WITPSerializer,
        responses={200: PartySerializer},
    )
    @action(methods=[HTTPMethod.PATCH], detail=True, url_path="confirmwitp")
    def update_party_with_witp(self, request: Request, pk: uuid.uuid4):
        """Assign witp code if there is no WITP code"""
        current_user = request.user
        role = current_user.groups.first()
        new_witp = WITPSerializer(data=request.data)
        if not new_witp.is_valid():
            raise exceptions.ValidationError(detail="WITP code not valid !")
        if is_ebs_team(role):
            try:
                party = Party.objects.get(pk=pk)
            except Party.DoesNotExist as e:
                logger.error(f"Party with id {pk!r} does not exist.")
                raise PartyNotFoundException from e
            if party.witp_code:
                return Response(
                    "Party already has a WITP code", status=status.HTTP_400_BAD_REQUEST
                )
            else:
                party.witp_code = new_witp.validated_data.get("witp_code")
                party.updated_by = request.user
                party.save()
                serialised_party = self.serializer_class(instance=party)
                return Response(serialised_party.data)
        raise PermissionDenied("You do not have permission to perform this action.")

    def destroy(self, request: Request, pk: uuid.UUID):
        obj = self.queryset.filter(pk=pk).first()
        if obj.status != StatusChoices.DRAFT:
            raise PermissionDenied()
        obj.delete()
        return Response(None, status=status.HTTP_200_OK)

    @extend_schema(request=PartySerializer)
    @action(methods=[HTTPMethod.PATCH], detail=True, url_path="update-with-witp")
    def after_approve_update(self, request: Request, pk: uuid.UUID) -> Response:
        """Update a party partially"""
        try:
            party = Party.objects.get(id=pk)
        except Party.DoesNotExist as exc:
            logger.error(f"Party with id {pk!r} does not exist.")
            raise PartyNotFoundException() from exc
        try:
            if party.status == StatusChoices.DRAFT:
                serializer = PartySerializer(
                    instance=party, data=request.data, partial=True
                )

                if not serializer.is_valid():
                    raise exceptions.ValidationError(serializer.error_messages)

                serializer.save()
                return Response(serializer.data)

            old_party = Party.objects.get(id=pk)
            old_contacts = old_party.contacts.all()
            old_attachments = old_party.attachments.all()
            old_extras = old_party.extras.all()
            old_dealing = old_party.dealing

            party.id = None
            party.pk = None
            party.created_by = request.user
            party.updated_by = request.user
            party.status = StatusChoices.DRAFT
            party.stage = None
            party.next_node = old_party
            party.save()

            # handle dealing
            old_dealing.id = None
            old_dealing.party = party
            old_dealing.save()

            # handle contacts
            for contact in old_contacts:
                contact.pk = None
                contact.party = party
                contact.save()

            # handle attachments
            for att in old_attachments:
                att.pk = None
                att.party = party
                att.save()

            # handle extras
            for ext in old_extras:
                ext.pk = None
                ext.party = party
                ext.save()

            serializer = PartySerializer(
                instance=party, data=request.data, partial=True
            )

            if not serializer.is_valid():
                raise exceptions.ValidationError(serializer.errors)

            serializer.save()

            return Response(serializer.data)
        except Exception as exc:
            logger.exception(exc)
            raise ServerError(str(exc)) from exc

    @action(methods=[HTTPMethod.GET], detail=True, url_path="prev-nodes")
    def party_prev_nodes(self, request: Request, pk: uuid.UUID):  # noqa: C901
        current_user: User = request.user
        role: Group = current_user.groups.first()

        try:
            party = Party.objects.get(id=pk)
        except Party.DoesNotExist as exc:
            logger.error(f"Party with id {pk!r} does not exist.")
            raise PartyNotFoundException() from exc

        qs = party.rev_nodes

        if current_user.is_management or role:
            qs = qs.filter(
                ~Q(status=StatusChoices.DRAFT)
                & (
                    Q(stage__iexact=role.name)
                    | Q(stage__iexact=StatusChoices.APPROVED)
                    | Q(stage__iexact=StatusChoices.REJECTED)
                )
            )

        paginator = self.pagination_class()
        paginator.set_page_size(request)
        paginated_queryset = paginator.paginate_queryset(qs.all(), request)
        serialized_data = self.serializer_class(instance=paginated_queryset, many=True)
        return paginator.get_paginated_response(serialized_data.data)
