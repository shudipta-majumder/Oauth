from django.db.models.signals import post_save
from django.dispatch import receiver

from core.constants import StatusChoices
from pms.models import CreditLimit, Party, ShipLocation

from .models import ApprovalQueue
from .process import (
    CreditLimitApproveProcess,
    EmptyProcess,
    PartyQueueApproveProcess,
    QueueRejectProcess,
    ShipLocApproveProcess,
)


class ObjectActionHandler:
    def __init__(self, core_object, approval_queue_obj):
        self.core_object = core_object
        self.queue = approval_queue_obj

    def run(self):
        if self.queue.status == StatusChoices.APPROVED:
            action_factory = ObjectTypeActionFactory(self.core_object, self.queue)
            return action_factory.get()
        elif self.queue.status == StatusChoices.REJECTED:
            return QueueRejectProcess(self.queue, self.core_object)
        else:
            return EmptyProcess(self.queue, self.core_object)


class ObjectTypeActionFactory:
    def __init__(self, core_object, approval_queue_obj):
        self.core_object = core_object
        self.queue = approval_queue_obj

    def get(self):
        if isinstance(self.core_object, Party):
            return PartyQueueApproveProcess(self.queue, self.core_object)
        if isinstance(self.core_object, CreditLimit):
            return CreditLimitApproveProcess(self.queue, self.core_object)
        if isinstance(self.core_object, ShipLocation):
            return ShipLocApproveProcess(self.queue, self.core_object)


@receiver(post_save, sender=ApprovalQueue)
def handle_post_save_approval(sender, instance: ApprovalQueue, created: bool, **kwargs):
    if not created:
        model_class = instance.content_type.model_class()
        model_object = model_class.objects.get(pk=instance.object_id)

        action = ObjectActionHandler(model_object, instance)
        process = action.run()
        process.execute()
