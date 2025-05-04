from dataclasses import asdict, dataclass
from logging import getLogger

import oracledb
from django.conf import settings
from oracledb.exceptions import DatabaseError
from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from .sql_query import party_addresses_sql

logger = getLogger(__name__)


class OracleServiceException(APIException):
    status_code = HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Oracle Database Connection Failed."
    default_code = "connection_error"


class PartyNotFoundException(APIException):
    status_code = HTTP_404_NOT_FOUND
    default_detail = "EBS Party does not exists."
    default_code = "party_error"


@dataclass(frozen=True)
class PartyAddress:
    party_id: int
    party_name: str
    witp_code: str
    org_id: int
    default_address: str
    all_address: str
    contact_person: str
    mobile_number: str


class ShipLocationService:
    @staticmethod
    def get_addresses_of_party(witp_code: str):
        try:
            with oracledb.connect(params=settings.EBS_CONN_PARAMS) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(party_addresses_sql, witp_code=witp_code)
                    results = (
                        asdict(PartyAddress(*address)) for address in cursor.fetchall()
                    )
        except DatabaseError as exc:
            logger.exception(exc)
            raise OracleServiceException(str(exc)) from exc
        logger.info(f"Retrieved party address for WITP code {witp_code!r}.")
        return results
