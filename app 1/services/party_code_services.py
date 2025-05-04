from abc import ABC, abstractmethod
from logging import getLogger

from pms.constants import PMSRecommendationStages
from recommendation_engine.models import ApprovalUser, RecommendationProcess

from ..models import Party

_logger = getLogger(__name__)


class BasePartyService(ABC):
    @abstractmethod
    def execute(self):
        raise NotImplementedError


class NewPartyCodeService(BasePartyService):
    def __init__(self, instance: Party):
        self.instance = instance
        self.new_party_code_all_ok_path = RecommendationProcess.objects.get(
            codename="new_code_all_ok"
        )
        self.new_party_code_partial_ok_path = RecommendationProcess.objects.get(
            codename="new_code_partial_ok"
        )

    def execute(self):
        all_ok = self.instance.has_all_required_docs()

        if all_ok:
            _logger.info(
                f"Creating 'all_ok' path for Party({self.instance!r}) with ID({self.instance.pk!r})."
            )
            return ApprovalUser().get_path_for(
                self.instance.system, self.new_party_code_all_ok_path
            )
        _logger.info(
            f"Creating 'partial_ok' path for Party({self.instance!r}) with ID({self.instance.pk!r})."
        )
        return ApprovalUser().get_path_for(
            self.instance.system, self.new_party_code_partial_ok_path
        )


class ExistingPartyCodeService(BasePartyService):
    def __init__(self, instance: Party):
        self.instance = instance

    def _tag_parent_party(self):
        self.instance.next_node.history_current_step = 2
        self.instance.next_node.history_current_stage = PMSRecommendationStages.INCHARGE
        self.instance.next_node.save()
        _logger.info(
            f"History tracked for {self.instance!r} with id={self.instance.pk}"
        )

    def execute(self):
        self._tag_parent_party()
        _logger.info(
            f"Creating 'existing_party' path for Party({self.instance!r}) with ID({self.instance.pk!r})."
        )
        return ApprovalUser().get_path_for(self.instance.system, self.instance.process)
