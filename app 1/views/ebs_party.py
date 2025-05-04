from dataclasses import asdict, dataclass
from datetime import date
from http import HTTPMethod
from logging import getLogger
from typing import Any, Dict

import oracledb
from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from oracledb.exceptions import DatabaseError
from rest_framework import exceptions, serializers, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from core.openapi_metadata.metadata import OpenApiTags
from core.renderer import CustomRenderer

logger = getLogger("pms.views.ebs_party")

__all__ = ["EbsPartyViewSet", "EbsPartyCollectionViewSet"]


class InvalidWitpCodeException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Not valid integer number.")
    default_code = "value_error"


class OracleServiceException(exceptions.APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("Oracle Database Connection Failed.")
    default_code = "connection_error"


class PartyNotFoundException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("EBS Party does not exists.")
    default_code = "party_error"


class SerialNotFoundException(exceptions.APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Serial ID not found.")
    default_code = "not_found"


@dataclass(frozen=True)
class EbsProductSerial:
    inventory_item_id: str
    item_code: str
    description: str
    serial_number: str
    product_size: str
    hdd: str
    series: str
    processor: str
    ram: str


class EbsProductSerialSerializer(serializers.Serializer):
    inventory_item_id = serializers.CharField(max_length=255)
    item_code = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=255)
    serial_number = serializers.CharField(max_length=255)
    product_size = serializers.CharField(max_length=255)
    hdd = serializers.CharField(max_length=255)
    series = serializers.CharField(max_length=255)
    processor = serializers.CharField(max_length=255)
    ram = serializers.CharField(max_length=255)


@dataclass(frozen=True)
class EbsParty:
    id: int
    account_number: str
    account_name: str
    party_name: str
    party_present_addr: str
    ph_address: str
    customer_category: str
    creation_date: date
    division: str
    district: str
    police_station: str
    last_name: str
    ph_contact: str
    zone: str
    area: str
    party_category: str
    nid: str
    tin: str
    bin: str
    birth_day: date
    primary_invest: str
    present_size: str
    commitment_size: str
    email_address: str
    sales_person: str


@dataclass(frozen=True)
class EbsPartyShipLocationInfo:
    party_id: str
    party_number: str
    party_name: str
    witp_code: str
    address: str


class EbsPartyShipLocationSerializer(serializers.Serializer):
    party_name = serializers.CharField()
    party_id = serializers.CharField()
    party_number = serializers.CharField()


class EbsPartySerializer(serializers.Serializer):
    party_id = serializers.IntegerField()
    account_number = serializers.CharField(max_length=255)
    account_name = serializers.CharField(max_length=255)
    party_name = serializers.CharField(max_length=255)
    address1 = serializers.CharField(max_length=255)
    ph_address = serializers.CharField(max_length=255)
    customer_category = serializers.CharField(max_length=255)
    creation_date = serializers.DateField()
    division = serializers.CharField(max_length=255)
    district = serializers.CharField(max_length=255)
    police_station = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    ph_contact = serializers.CharField(max_length=255)
    zone = serializers.CharField(max_length=255)
    area = serializers.CharField(max_length=255)
    exclusive_status = serializers.CharField(max_length=255)
    nid = serializers.CharField(max_length=255)
    tin = serializers.CharField(max_length=255)
    bin = serializers.CharField(max_length=255)
    birth_day = serializers.DateField()
    primary_invest = serializers.CharField(max_length=255)
    present_size = serializers.CharField(max_length=255)
    commitment_size = serializers.CharField(max_length=255)
    email_address = serializers.EmailField()
    created_by = serializers.CharField(max_length=255)


EBS_PARTY_QUERY_STRING = """
SELECT DISTINCT
    HP.PARTY_ID,
    HCA.ACCOUNT_NUMBER,
    HCA.ACCOUNT_NAME,
    HP.PARTY_NAME,
    HP.ADDRESS1,
    LOC.ADDRESS_LINES_PHONETIC AS PH_ADDRESS,
    HCA.SALES_CHANNEL_CODE AS Customer_Category,
    TRUNC(HP.CREATION_DATE) AS CREATION_DATE,
    HP.ADDRESS3 AS Division,
    HP.ADDRESS4 AS District,
    HP.POSTAL_CODE AS Police_Station,
    PH.LAST_NAME,
    PH.PHONE_NUMBER AS PH_CONTACT,
    HP.ATTRIBUTE1 AS ZONE,
    HP.ATTRIBUTE2 AS AREA,
    HCA.CUSTOMER_CLASS_CODE AS Exclusive_Status,
    PS.ADDRESSEE AS NID,
    HP.JGZZ_FISCAL_CODE AS TIN,
    HP.TAX_REFERENCE AS BIN,
    PH.JOB_TITLE AS Birth_Day,
    HP.DUNS_NUMBER AS Primary_Invest,
    HP.YEAR_ESTABLISHED AS Present_Size,
    HP.MISSION_STATEMENT AS Commitment_Size,
    HP.EMAIL_ADDRESS,
    APPS.SOFTLN_COM_PKG.GET_EMP_NAME_FROM_USER_ID(HP.CREATED_BY) AS Created_By
FROM
    HZ_PARTIES HP
    LEFT JOIN HZ_CUST_ACCOUNTS HCA ON HP.PARTY_ID = HCA.PARTY_ID
    LEFT JOIN APPS.SOFTLN_AR_CONTACTS_PHONE_V PH ON PH.CUSTOMER_ID = HCA.CUST_ACCOUNT_ID
    JOIN APPS.HZ_PARTY_SITES PS ON PS.PARTY_ID = HP.PARTY_ID
    JOIN APPS.HZ_LOCATIONS LOC ON PS.LOCATION_ID = LOC.LOCATION_ID
WHERE
    HP.PARTY_TYPE = 'ORGANIZATION'
    AND HP.PARTY_ID = :party_id
ORDER BY
    HP.PARTY_ID
"""

EBS_PARTY_QUERY_STRING_WITP = """
SELECT DISTINCT
    HP.PARTY_ID AS ID,
    HCA.ACCOUNT_NUMBER,
    HCA.ACCOUNT_NAME,
    HP.PARTY_NAME,
    HP.ADDRESS1 AS party_present_addr,
    LOC.ADDRESS_LINES_PHONETIC AS PH_ADDRESS,
    HCA.SALES_CHANNEL_CODE AS Customer_Category,
    TRUNC(HP.CREATION_DATE) AS CREATION_DATE,
    HP.ADDRESS3 AS Division,
    HP.ADDRESS4 AS District,
    HP.POSTAL_CODE AS Police_Station,
    PH.LAST_NAME,
    PH.PHONE_NUMBER AS PH_CONTACT,
    HP.ATTRIBUTE1 AS ZONE,
    HP.ATTRIBUTE2 AS AREA,
    HCA.CUSTOMER_CLASS_CODE AS party_category,
    PS.ADDRESSEE AS NID,
    HP.JGZZ_FISCAL_CODE AS TIN,
    HP.TAX_REFERENCE AS BIN,
    PH.JOB_TITLE AS Birth_Day,
    HP.DUNS_NUMBER AS Primary_Invest,
    HP.YEAR_ESTABLISHED AS Present_Size,
    HP.MISSION_STATEMENT AS Commitment_Size,
    HP.EMAIL_ADDRESS,
    APPS.SOFTLN_COM_PKG.GET_EMP_NAME_FROM_USER_ID(HP.CREATED_BY) AS sales_person
FROM
    HZ_PARTIES HP
    LEFT JOIN HZ_CUST_ACCOUNTS HCA ON HP.PARTY_ID = HCA.PARTY_ID
    LEFT JOIN APPS.SOFTLN_AR_CONTACTS_PHONE_V PH ON PH.CUSTOMER_ID = HCA.CUST_ACCOUNT_ID
    JOIN APPS.HZ_PARTY_SITES PS ON PS.PARTY_ID = HP.PARTY_ID
    JOIN APPS.HZ_LOCATIONS LOC ON PS.LOCATION_ID = LOC.LOCATION_ID
WHERE
    HP.PARTY_TYPE = 'ORGANIZATION'
    AND HCA.ACCOUNT_NUMBER = :witp_code
"""

PARY_BASIC_INFORMATION_QUERY = """
SELECT
	DISTINCT PARTY.PARTY_ID,
	PARTY.PARTY_NUMBER,
	PARTY.PARTY_NAME,
	CUST_ACCT.ACCOUNT_NUMBER AS WITP_CODE,
	LOC.ADDRESS1 AS ADDRESS
FROM
	APPS.HZ_PARTIES PARTY,
	APPS.HZ_CUST_ACCOUNTS CUST_ACCT,
	APPS.HZ_CUST_SITE_USES_ALL SITE_USE,
	APPS.HZ_CUST_ACCT_SITES_ALL ACCT_USE,
	APPS.HZ_PARTY_SITES PS,
	APPS.HZ_LOCATIONS LOC,
	APPS.SOFTLN_AR_CUSTOMERS_ALL_V CUST,
	apps.ZX_PARTY_TAX_PROFILE TP,
	APPS.HZ_CUST_PROFILE_AMTS HCPA,
	APPS.SOFTLN_AR_CONTACTS_PHONE_V ACP
WHERE
	PARTY.PARTY_ID = CUST_ACCT.PARTY_ID
	AND PARTY.PARTY_ID = CUST.PARTY_ID
	AND PARTY.PARTY_ID = TP.PARTY_ID
	AND CUST_ACCT.cust_account_id = HCPA.cust_account_id(+)
	AND SITE_USE.CUST_ACCT_SITE_ID = ACCT_USE.CUST_ACCT_SITE_ID
	AND CUST_ACCT.CUST_ACCOUNT_ID = ACCT_USE.CUST_ACCOUNT_ID
	AND ACCT_USE.PARTY_SITE_ID = PS.PARTY_SITE_ID
	AND PS.LOCATION_ID = LOC.LOCATION_ID
	AND ACP.CUSTOMER_ID(+) = CUST.CUSTOMER_ID
	AND CUST_ACCT.ACCOUNT_NUMBER = :witp_code
	AND SITE_USE.SITE_USE_CODE = 'SHIP_TO'
	AND SITE_USE.LOCATION = 'Witp'
	AND PARTY.STATUS = 'A'
	AND CUST_ACCT.STATUS = 'A'
	AND SITE_USE.STATUS = 'A'
	AND ACCT_USE.STATUS = 'A'
"""


def fetch_basic_party(witp_code: str) -> Dict[str, Any]:
    try:
        with oracledb.connect(params=settings.EBS_CONN_PARAMS) as connection:
            with connection.cursor() as cursor:
                cursor.execute(PARY_BASIC_INFORMATION_QUERY, witp_code=witp_code)
                queryset = cursor.fetchone()
    except DatabaseError as exc:
        logger.exception(exc)
        raise OracleServiceException(str(exc)) from exc

    if not queryset:
        logger.warning(f"No party found with WITP code {witp_code!r}.")
        raise PartyNotFoundException
    result = asdict(EbsPartyShipLocationInfo(*queryset))
    logger.info(f"Retrieved party information for WITP code {witp_code!r}.")
    return result


@extend_schema(tags=[OpenApiTags.EBS_ROUTES])
class EbsPartyViewSet(ViewSet):
    # TODO: Need to give the Response serializer type
    authentication_classes = []
    permission_classes = []
    pagination_class = None
    paginator = None
    required_scopes = ["read"]
    renderer_classes = [
        CustomRenderer,
    ]

    @extend_schema(
        responses={200: EbsPartyShipLocationSerializer},
        parameters=[
            OpenApiParameter(
                name="id", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
            )
        ],
    )
    @method_decorator(cache_page(60 * 60 * 4))
    def retrieve(self, request: Request, pk: int) -> Response:
        """Retrieve an existing Party Information with WITP CODE"""
        response = fetch_basic_party(pk)
        return Response(response)

    @extend_schema(
        responses={200: EbsPartySerializer},
        parameters=[
            OpenApiParameter(
                name="id", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
            )
        ],
    )
    @method_decorator(cache_page(60 * 60 * 4))
    @action(detail=True, methods=[HTTPMethod.GET], url_path="partyid")
    def retrieve_with_party_id(self, request: Request, pk: int):
        """Retrieve an existing Party Information with Party ID"""
        try:
            pk = int(pk)
        except ValueError as exc:
            logger.error(f"Invalid party ID: {pk!r}. {str(exc)!r}")
            raise InvalidWitpCodeException(f"{pk!r} is not a valid number.") from exc

        try:
            with oracledb.connect(params=settings.EBS_CONN_PARAMS) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(EBS_PARTY_QUERY_STRING, party_id=pk)
                    queryset = cursor.fetchall()
        except DatabaseError as exc:
            logger.exception(exc)
            raise OracleServiceException(str(exc)) from exc
        if not queryset:
            logger.warning(f"No party found with party ID {pk!r}.")
            raise PartyNotFoundException
        response = [asdict(EbsParty(*data)) for data in queryset]
        logger.info(f"Retrieved party information for party ID {pk!r}.")
        return Response(response)


@extend_schema(tags=[OpenApiTags.EBS_ROUTES])
class EbsPartyCollectionViewSet(ViewSet):
    authentication_classes = []
    permission_classes = []
    pagination_class = None
    paginator = None
    required_scopes = ["read"]
    renderer_classes = [
        CustomRenderer,
    ]

    def dict_provider(self, cursor):
        """helper function to get the tuples as dict"""
        column_names = [d[0] for d in cursor.description]

        def create_row(*args):
            return dict(zip(column_names, args))

        return create_row

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id", type=OpenApiTypes.STR, location=OpenApiParameter.PATH
            )
        ],
    )
    @method_decorator(cache_page(60 * 60 * 4))
    @action(detail=True, methods=[HTTPMethod.GET], url_path="bywitp")
    def retrieve_with_party_id(self, request: Request, pk: int):
        """Retrieve an existing Party Information with Party ID"""
        from .ebs_collection_query import COLLECTION_QUERY_STR

        try:
            with oracledb.connect(params=settings.EBS_CONN_PARAMS) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(COLLECTION_QUERY_STR, witp_code=pk)
                    cursor.rowfactory = self.dict_provider(cursor)
                    queryset = cursor.fetchall()
        except DatabaseError as exc:
            logger.exception(exc)
            raise OracleServiceException(str(exc)) from exc
        if not queryset:
            logger.warning(f"No party found with party ID {pk!r}.")
            raise PartyNotFoundException
        logger.info(f"Retrieved party information for party ID {pk!r}.")

        return Response(queryset)
