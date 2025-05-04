from abc import ABC, abstractmethod
from datetime import date, timedelta
from logging import getLogger

from django.db.models import DateTimeField, ExpressionWrapper, F, QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status

from ..exceptions import PartyNotFoundException
from ..models import Guarantee, Party, SecurityCheque

_logger = getLogger(__name__)


class ApplicationBlockedException(exceptions.APIException):
    status_code = status.HTTP_412_PRECONDITION_FAILED
    default_detail = _("Application is blocked due to Cheque or Guarantor Expired !")
    default_code = "expired"


class ApplicationDocHandlerAbstract(ABC):
    """Abstract class of the Application Blocker Service"""

    @abstractmethod
    def run_check(self, witp_code: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_expired(self, witp_code: str) -> bool:
        raise NotImplementedError


class CreditLimitExpiredDocHandler(ApplicationDocHandlerAbstract):
    """An application blocker for credit limit. it's soul responsibility is handle the
    business logic for the blocking.
    """

    def __init__(self, instance: Party | None = None):
        self.party = instance

    def _check_date_expiry(self, dt: date) -> bool:
        """doc should be considered as expired if doc date is smaller and equal to current date"""
        if not dt:
            return False
        return dt <= timezone.now().date()

    def _get_party(self, witp_code: str):
        if self.party and isinstance(self.party, Party):
            return self.party
        try:
            return Party.objects.get(witp_code=witp_code)
        except Party.DoesNotExist as exc:
            _logger.error(str(exc))
            raise PartyNotFoundException from exc

    @staticmethod
    def _get_expired_cheques(qs: QuerySet[SecurityCheque]):
        six_months_later = ExpressionWrapper(
            F("cheque_maturity_date") + timedelta(days=6 * 30),
            output_field=DateTimeField(),
        )
        result = qs.annotate(six_months_later=six_months_later).filter(
            six_months_later__lte=timezone.now()
        )
        return result

    @staticmethod
    def _get_expired_guarantors(qs: QuerySet[Guarantee]):
        return qs.filter(expiry_date__lte=timezone.now())

    def _get_trade_license_expired(self, instance: Party):
        expired = self._check_date_expiry(instance.trade_license_expires)
        if expired:
            return instance.trade_license_expires
        return None

    def _get_general_att_expired(self, instance: Party):
        attachment_row = instance.attachments.first()
        if not attachment_row:
            return None
        expired = self._check_date_expiry(attachment_row.expiry_date_general_attachment)
        if not expired:
            return None
        return attachment_row.expiry_date_general_attachment

    def _check_expiry(self, witp_code: str):
        # as automatically a init stage credit limit is created, it will
        # search with none value so it can be duplicate.
        if not bool(witp_code):
            return False
        _party = self._get_party(witp_code)

        cheque_expired = self._get_expired_cheques(
            _party.security_cheques.all()
        ).exists()
        guarator_expired = self._get_expired_guarantors(
            _party.guarantee_collections.all()
        ).exists()

        return cheque_expired or guarator_expired

    def run_check(self, witp_code: str) -> None:
        """check for cheques and gurantors expiry date"""

        if self._check_expiry(witp_code):
            raise ApplicationBlockedException()

    def is_expired(self, witp_code: str) -> bool:
        """as like `run_check` func. Only difference has this func has return of boolean type"""

        if self._check_expiry(witp_code):
            return True
        return False

    def export_for_ui(self, witp_code: str):
        try:
            _party = self._get_party(witp_code)
            _cheques = _party.security_cheques.all()
            _guarantors = _party.guarantee_collections.all()

            payload = {
                "expired_cheques": self._get_expired_cheques(_cheques)
                if _cheques.exists()
                else [],
                "expired_guarantors": self._get_expired_guarantors(_guarantors)
                if _guarantors.exists()
                else [],
                "expired_trade_license": self._get_trade_license_expired(_party),
                "expired_attachment": self._get_general_att_expired(_party),
            }
            return payload
        except Exception as exc:
            _logger.error("Error While Exporting UI")
            _logger.exception(exc)
            raise exc from exc
