from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from logging import getLogger
from typing import List

import oracledb
from django.conf import settings
from django.db.models import Sum
from oracledb.exceptions import DatabaseError
from rest_framework import exceptions, status

from recommendation_engine.models import ApprovalUser, RecommendationProcess

from ..models import CreditLimit, EbsCollectionDetail
from .sql_query import (
    max_invoice_day_count_sql,
    party_collections_sql,
    party_default_addr_sql,
    party_grading_sql,
    party_status_sql,
)

_logger = getLogger(__name__)

limit_ratio_a_category = 5_00_000
limit_ratio_b_category = 3_00_000
limit_ratio_c_category = 1_50_000
MAX_DUE_DAYS = 30


def _fetch_row(conn: oracledb.Connection, sql: str, witp_code: str):
    with conn.cursor() as cur:
        cur.execute(sql, witp_code=str(witp_code))
        return cur.fetchone()


def _fetch_rows(conn: oracledb.Connection, sql, witp_code):
    with conn.cursor() as cur:
        cur.execute(sql, witp_code=str(witp_code))
        return cur.fetchall()


class OracleServiceException(exceptions.APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Oracle Database Connection Failed."
    default_code = "connection_error"


@dataclass
class PartyGradeRow:
    witp_code: str | None = None
    party_name: str | None = None
    is_all_doc_up: str | None = None
    rating_certificate: str | None = None
    party_status: str | None = None
    cus_category: str | None = None
    closing_balance: float = 0
    average_collection_ratio: int = 0
    grade: str | None = None


class CreditLimitService:
    start_date = datetime.now()
    end_date = start_date - timedelta(days=30)

    @classmethod
    def get_orcl_date_format(cls, date: datetime) -> str:
        return date.strftime("%d-%b-%Y")

    @classmethod
    def dict_provider(cls, cursor):
        """helper function to get the tuples as dict"""
        column_names = [str.lower(d[0]) for d in cursor.description]

        def create_row(*args):
            return dict(zip(column_names, args))

        return create_row

    @staticmethod
    @lru_cache(maxsize=48)
    def get_party_grading(
        witp_code: str, connection: oracledb.Connection | None = None
    ) -> PartyGradeRow:
        """party category/grading/rating query. based on this return the approval path
        is going to have one more step added.
        """
        try:
            if connection:
                row = _fetch_row(connection, party_grading_sql, witp_code)
            else:
                with oracledb.connect(params=settings.EBS_CONN_PARAMS) as con:
                    row = _fetch_row(con, party_grading_sql, witp_code)
        except oracledb.DatabaseError as exc:
            _logger.exception(exc)
            raise OracleServiceException from exc

        if not row:
            return PartyGradeRow()

        result = PartyGradeRow(*row)

        return result

    @staticmethod
    def get_max_inv_due_count(
        witp_code: str, connection: oracledb.Connection | None = None
    ):
        try:
            if connection:
                row = _fetch_row(connection, max_invoice_day_count_sql, witp_code)
            else:
                with oracledb.connect(params=settings.EBS_CONN_PARAMS) as connection:
                    row = _fetch_row(connection, max_invoice_day_count_sql, witp_code)
        except oracledb.DatabaseError as exc:
            _logger.exception(exc)
            raise OracleServiceException from exc
        return row[-1] if row[-1] else 0

    @classmethod
    @lru_cache(maxsize=48)
    def get_party_status(
        cls,
        witp_code: str,
        start_date: datetime = start_date,
        end_date: datetime = end_date,
        connection: oracledb.Connection | None = None,
    ) -> str:
        """party status according to last 6 months of transaction of a party"""

        def _get_data():
            with connection.cursor() as cursor:
                cursor.execute(
                    party_status_sql,
                    WITP_CODE=witp_code,
                    P_START_DATE=cls.get_orcl_date_format(end_date),
                    P_END_DATE=cls.get_orcl_date_format(start_date),
                )
                return cursor.fetchone()

        try:
            if connection:
                row = _get_data()
            else:
                with oracledb.connect(params=settings.EBS_CONN_PARAMS) as connection:
                    row = _get_data()
        except oracledb.DatabaseError as exc:
            _logger.exception(exc)
            _logger.error(cls.get_orcl_date_format(start_date))
            _logger.error(cls.get_orcl_date_format(end_date))
            raise OracleServiceException from exc

        if not row:
            return "WATCHFUL"

        return row[-1]

    @staticmethod
    @lru_cache(maxsize=48)
    def get_party_default_addr(
        witp_code: str, connection: oracledb.Connection | None = None
    ) -> str:
        """party status according to last 6 months of transaction of a party"""
        try:
            if connection:
                queryset = _fetch_row(connection, party_default_addr_sql, witp_code)
            else:
                with oracledb.connect(params=settings.EBS_CONN_PARAMS) as connection:
                    queryset = _fetch_row(connection, party_default_addr_sql, witp_code)
        except oracledb.DatabaseError as exc:
            _logger.exception(exc)
            raise OracleServiceException from exc
        if not queryset:
            _logger.warning(
                f"Party default address not found with WITP({witp_code!r})."
            )
            return "NOT FOUND"
        return queryset[-1]

    @classmethod
    def get_party_collections(
        cls, witp_code: str, connection: oracledb.Connection | None = None
    ) -> List:
        """party status according to last 6 months of transaction of a party"""

        def _get_data():
            with connection.cursor() as cursor:
                cursor.execute(party_collections_sql, witp_code=witp_code)
                cursor.rowfactory = cls.dict_provider(cursor)
                return cursor.fetchall()

        try:
            if connection:
                queryset = _get_data()
            else:
                with oracledb.connect(params=settings.EBS_CONN_PARAMS) as connection:
                    queryset = _get_data()
        except DatabaseError as exc:
            _logger.exception(exc)
            _logger.error("Collection details fetch error due to oracle exception.")
        else:
            if not queryset:
                _logger.warning(
                    f"Collection details not found for party ID {witp_code!r}."
                )

            return queryset

    @staticmethod
    def create_party_collections(instance, collections):
        instance.collection_details.all().delete()
        for col in collections:
            col["credit_limit"] = instance
            collection = EbsCollectionDetail(**col)
            collection.save()

    @staticmethod
    def set_credit_limit_extra_details(
        instance: CreditLimit,
        grade: str,
        due_count: int,
        party_status: str,
        default_addr: str,
    ):
        instance.grade = grade
        instance.invoice_due_max_days = due_count
        instance.party_status = party_status
        instance.party_address = default_addr
        instance.save()

    @classmethod
    def _generate_approval_chain(cls, instance: CreditLimit):
        if not instance.proposed_limit_wcl:
            instance.proposed_limit_wcl = Decimal(0.0)

        if not instance.proposed_limit_wdc:
            instance.proposed_limit_wdc = Decimal(0.0)

        total = instance.proposed_limit_wdc + instance.proposed_limit_wcl

        grade_a_path = RecommendationProcess.objects.get(
            codename="revise_credit_limit_a"
        )
        grade_c_path = RecommendationProcess.objects.get(
            codename="revise_credit_limit_c"
        )

        closing_balance_sum = instance.collection_details.aggregate(
            Sum("closing_balance")
        )["closing_balance__sum"]

        if instance.grade.upper() == "A":
            if (
                closing_balance_sum < 0 or instance.invoice_due_max_days <= MAX_DUE_DAYS
            ) and total <= limit_ratio_a_category:
                _logger.info(
                    f"Generating 'A' path for CreditLimit({instance} | {instance.id})"
                )
                return ApprovalUser().get_path_for(instance.system, grade_a_path)
        elif instance.grade.upper() == "B":
            if (
                closing_balance_sum < 0 or instance.invoice_due_max_days <= MAX_DUE_DAYS
            ) and total <= limit_ratio_b_category:
                _logger.info(
                    f"Generating 'B' path for CreditLimit({instance} | {instance.id})"
                )
                return ApprovalUser().get_path_for(instance.system, grade_a_path)
        elif instance.grade.upper() == "C":
            if (
                closing_balance_sum < 0 or instance.invoice_due_max_days <= MAX_DUE_DAYS
            ) and total <= limit_ratio_c_category:
                _logger.info(
                    f"Generating 'C' path for CreditLimit({instance} | {instance.id})"
                )
                return ApprovalUser().get_path_for(instance.system, grade_a_path)
        else:
            pass
        _logger.info(
            f"Generating 'C' path for CreditLimit({instance} | {instance.id}) for Non-Categorized."
        )
        return ApprovalUser().get_path_for(instance.system, grade_c_path)

    @classmethod
    def get_credit_limit_approval_path(cls, instance: CreditLimit, row: PartyGradeRow):
        if instance.grade.upper().strip() in ("A", "B", "C"):
            return cls._generate_approval_chain(instance)

        # here need the implementation of security cheque validation
        cheque_exists = instance.creditlimitdetail_set.filter(
            micr_cheque__isnull=False
        ).exists()
        stamp_exists = (
            bool(instance.judicial_stamp.name) if instance.judicial_stamp else False
        )

        if row.is_all_doc_up is None:
            row.is_all_doc_up = ""

        if row.average_collection_ratio is None:
            row.average_collection_ratio = 0

        if (
            row.is_all_doc_up.upper().strip() in ("YES", "OTHERS")
            and (
                row.average_collection_ratio >= 100 or row.average_collection_ratio < 0
            )
            and (
                row.rating_certificate in ("AAA", "AA", "A")
                or cheque_exists
                or stamp_exists
            )
        ):
            _logger.info(
                f"Changed grade {row.grade}  => 'A' for CreditLimit({instance} | {instance.id})"
            )
            row.grade = "A"
        elif (
            row.is_all_doc_up.upper().strip() in ("YES", "OTHERS")
            and (row.average_collection_ratio >= 80 or row.average_collection_ratio < 0)
            and (
                row.rating_certificate in ("AAA", "AA", "A", "BBB")
                or cheque_exists
                or stamp_exists
            )
        ):
            _logger.info(
                f"Changed grade {row.grade}  => 'B' for CreditLimit({instance} | {instance.id})"
            )
            row.grade = "B"
        elif (
            row.is_all_doc_up.upper().strip() in ("YES", "OTHERS")
            and (row.average_collection_ratio >= 60 or row.average_collection_ratio < 0)
            and (
                row.rating_certificate in ("AAA", "AA", "A", "BBB", "BB")
                or cheque_exists
                or stamp_exists
            )
        ):
            _logger.info(
                f"Changed grade {row.grade}  => 'C' for CreditLimit({instance} | {instance.id})"
            )
            row.grade = "C"
        else:
            # no change required to grade
            _logger.info(
                f"Grade is unchanged for CreditLimit({instance} | {instance.id})"
            )
            pass
        instance.grade = row.grade
        instance.ebs_info_pulled = True
        return cls._generate_approval_chain(instance)
