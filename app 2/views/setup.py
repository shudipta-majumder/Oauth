from logging import getLogger

from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework.generics import ListAPIView

from core.openapi_metadata.metadata import OpenApiTags
from core.permissions import UserAccessControl

from ..models.tender import Ministry, Participant, Team, TenderType
from ..serializers.setup_serializers import (
    MinistrySerializer,
    ParticipantSerializer,
    TeamSerializer,
    TenderTypeSerializer,
)

logger = getLogger(__name__)


# This views are only for retriving the list of team name, ministry name, tender-type name.
# There is no need of any other method like create, update, delete.
# If this project needs to add or delete or update any team, ministry, tender-type then someone needs to go to admin panel to do so.


@extend_schema(tags=[OpenApiTags.TMS_SETUP])
class TeamListAPI(ListAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    pagination_class = None
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def get(self, request, *args, **kwargs):
        logger.info("TeamListAPI accessed")
        try:
            logger.debug("Querying Team objects")
            response = super().get(request, *args, **kwargs)
            logger.info("Successfully retrieved Team list")
            return response
        except Exception as e:
            logger.error(f"Error retrieving Team list: {e}")
            raise


@extend_schema(tags=[OpenApiTags.TMS_SETUP])
class MinistryListAPI(ListAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    pagination_class = None
    queryset = Ministry.objects.all()
    serializer_class = MinistrySerializer

    def get(self, request, *args, **kwargs):
        logger.info("MinistryListAPI accessed")
        try:
            logger.debug("Querying Ministry objects")
            response = super().get(request, *args, **kwargs)
            logger.info("Successfully retrieved Ministry list")
            return response
        except Exception as e:
            logger.error(f"Error retrieving Ministry list: {e}")
            raise


@extend_schema(tags=[OpenApiTags.TMS_SETUP])
class TenderTypeListAPI(ListAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    pagination_class = None
    queryset = TenderType.objects.all()
    serializer_class = TenderTypeSerializer

    def get(self, request, *args, **kwargs):
        logger.info("TenderTypeListAPI accessed")
        try:
            logger.debug("Querying TenderType objects")
            response = super().get(request, *args, **kwargs)
            logger.info("Successfully retrieved TenderType list")
            return response
        except Exception as e:
            logger.error(f"Error retrieving TenderType list: {e}")
            raise


@extend_schema(tags=[OpenApiTags.TMS_SETUP])
class ParticipantsListAPI(ListAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    pagination_class = None
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
