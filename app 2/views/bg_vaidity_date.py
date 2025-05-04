from logging import getLogger

from drf_spectacular.utils import extend_schema
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from rest_framework.generics import ListCreateAPIView

from core.openapi_metadata.metadata import OpenApiTags
from core.permissions import UserAccessControl

from ..models.tender import BGValidityDate
from ..serializers.bg_validity_date import BGValidityDateSerializer

logger = getLogger(__name__)


@extend_schema(tags=[OpenApiTags.TMS_BG_EXTENDED_DATE])
class BGValidityDateListCreateView(ListCreateAPIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [UserAccessControl]
    queryset = BGValidityDate.objects.all()
    serializer_class = BGValidityDateSerializer
