from abc import ABC
from logging import getLogger
from typing import Generic, TypeVar

from core.constants import StatusChoices
from pms.constants import EXISTING_PARTY
from pms.models import CreditLimit, Party, ShipLocation

from .models import ApprovalQueue, ApprovalStep, RecommendationProcess

_logger = getLogger(__name__)

T = TypeVar("T")


class BaseProcess(ABC, Generic[T]):
    def __init__(self, approval_instance: ApprovalQueue, obj: T):
        self.approval_instance = approval_instance
        self.instance = obj

    def __get_model_class(self):
        return self.approval_instance.content_type.model_class()

    def __set_model_object(self):
        return self.__get_model_class().objects.get(pk=self.approval_instance.object_id)

    def set_status(self, status: str):
        """set the current instance status"""
        self.instance.status = status

    def set_next_stage(self, stage: str):
        """send the current instance to next stage"""
        self.instance.stage = stage
        self.instance.save()

    def execute(self):
        """Execute the Process according to model business policies"""
        raise NotImplementedError


class PartyQueueApproveProcess(BaseProcess[Party]):
    def _change_party_state(self, process: RecommendationProcess):
        """set the new party to existing process after all approved"""
        self.instance.process = process
        _logger.info(f"Party({self.instance}) process has been marked as existing.")

    def _change_contacts_state(self):
        """set the contacts to existing after all approved"""
        self.instance.contacts.filter(is_existing=False).update(is_existing=True)
        _logger.info(f"Party({self.instance}) contacts has been marked as existing.")

    def _reset_stepper_index(self):
        self.instance.stepper_index = 0

    def _set_party_archived(self, party: Party):
        party.status = StatusChoices.ARCHIVED
        party.next_node = self.instance
        party.history_current_step = None
        party.history_current_stage = None
        party.save()
        _logger.info(
            f"Party({party}) with ID({party.id}) staged to {StatusChoices.ARCHIVED.title()}"
        )

    def _do_existing_party_code_process(self):
        try:
            parent = self.instance.next_node
            if parent:
                self._set_party_archived(parent)
                self.instance.next_node = None
        except Exception as exc:
            _logger.exception(exc)

    def _trace_child_party(self, next_node: ApprovalStep):
        self.instance.next_node.history_current_step = next_node.forward_step
        self.instance.next_node.history_current_stage = next_node.codename.lower()
        self.instance.next_node.save()
        _logger.info(f"Party({self.instance})'s next node history is updated.")

    def execute(self):
        first_pending_queue = self.approval_instance.get_first_pending_node()

        process_instance = RecommendationProcess.objects.get(codename=EXISTING_PARTY)
        # there are no pending approval nodes
        if not first_pending_queue:
            _logger.info(
                f"Party({self.instance}) queues action are done. initiating later process."
            )
            if process_instance == self.instance.process:
                _logger.info(
                    f"Party({self.instance}) is from existing process. calling existing party code process."
                )
                self._do_existing_party_code_process()
            else:
                _logger.info(
                    f"Party({self.instance}) is new party. calling party state change."
                )
                self._change_party_state(process_instance)
                self._change_contacts_state()

            self._reset_stepper_index()
            self.set_status(StatusChoices.APPROVED)
            self.set_next_stage(StatusChoices.APPROVED)
            _logger.info(f"Party({self.instance}) work cycle has been completed.")
            return

        if process_instance == self.instance.process:
            self._trace_child_party(first_pending_queue.node.approval_step)

        # handle pending approval
        current_stage = first_pending_queue.stage_name()
        self.set_next_stage(current_stage)
        _logger.info(
            f"Party({self.instance}) stage changed to {self.instance.stage.title()}"
        )


class CreditLimitApproveProcess(BaseProcess[CreditLimit]):
    def execute(self):
        first_pending_queue = self.approval_instance.get_first_pending_node()

        if not first_pending_queue:
            self.set_status(StatusChoices.APPROVED)
            self.set_next_stage(StatusChoices.APPROVED)
            _logger.info(f"CreditLimit({self.instance} work cycle has been completed.")
            return

        current_stage = first_pending_queue.stage_name()
        self.set_next_stage(current_stage)
        _logger.info(
            f"CreditLimit({self.instance}) stage changed to {self.instance.stage.title()}"
        )


class ShipLocApproveProcess(BaseProcess[ShipLocation]):
    def execute(self):
        first_pending_queue = self.approval_instance.get_first_pending_node()

        if not first_pending_queue:
            self.set_status(StatusChoices.APPROVED)
            self.set_next_stage(StatusChoices.APPROVED)
            _logger.info(f"ShipLocation({self.instance} work cycle has been completed.")
            return

        current_stage = first_pending_queue.stage_name()
        self.set_next_stage(current_stage)
        _logger.info(
            f"ShipLocation({self.instance}) stage changed to {self.instance.stage.title()}"
        )


class QueueRejectProcess(BaseProcess):
    def execute(self):
        pending_nodes = self.approval_instance.get_nodes()

        node_ids = (node.pk for node in pending_nodes)

        self.approval_instance.mark_chain_rejected(node_ids)
        self.set_status(StatusChoices.REJECTED)
        self.set_next_stage(StatusChoices.REJECTED)
        _logger.info(
            f"Party({self.instance}) stage changed to {StatusChoices.REJECTED.title()}"
        )


class EmptyProcess(BaseProcess):
    def execute(self):
        _logger.info(
            f"Party({self.instance}) no process done for {self.approval_instance.status.title()} status."
        )
        pass
