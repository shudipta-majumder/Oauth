from logging import getLogger

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.constants import StatusChoices
from pms.constants import EXISTING_PARTY, PMSRecommendationStages
from recommendation_engine.models import (
    ApprovalQueue,
    ApprovalUser,
    RecommendationProcess,
)

from .models import (
    CreditLimit,
    Party,
    PartyAttachment,
    ShipLocation,
)
from .services.credit_limit_services import CreditLimitService
from .services.party_code_services import ExistingPartyCodeService, NewPartyCodeService
from .services.remove_media_services import MediaRemover

_logger = getLogger(__name__)


def has_submitted(instance) -> bool:
    """Check if the given instance is submitted and stage doesn't have values"""
    return instance.status == StatusChoices.SUBMITTED and (
        instance.stage is None or instance.stage == ""
    )


class PartyQueueFactory:
    def __init__(self, instance: Party):
        self.process = RecommendationProcess.objects.get(codename=EXISTING_PARTY)
        self.instance = instance

    def get(self):
        if self.instance.process != self.process:
            new_party = NewPartyCodeService(self.instance)
            return new_party.execute()
        else:
            ex_party = ExistingPartyCodeService(self.instance)
            return ex_party.execute()


def generate_approval_chain(instance: Party | CreditLimit | ShipLocation, **kwargs):
    """Creates an approval path queue after getting the instance system & process type"""

    def _remove_existing_queues():
        existing_queues = ApprovalQueue.objects.filter(object_id=instance.id)
        if existing_queues.exists():
            existing_queues.delete()
            _logger.info(
                f"Deleted existing queues for {instance!r} with ID({instance.pk})"
            )

    def _create_queues():
        content_type = ContentType.objects.get_for_model(instance)
        queues_model = []
        for queue in queues:
            queues_model.append(
                ApprovalQueue(
                    node=queue, content_type=content_type, object_id=instance.id
                )
            )
        ApprovalQueue.objects.bulk_create(queues_model)
        _logger.info(f"Approval Queues created for Instance({instance!r})")

    def _send_to_next_stage():
        instance.stage = PMSRecommendationStages.INCHARGE
        instance.status = StatusChoices.PENDING
        instance.save()
        _logger.info(
            f"Migrated the current  Instance({instance!r}) with ID({instance.pk!r}) to {instance.stage.title()!r} stage."
        )

    if isinstance(instance, Party):
        factory = PartyQueueFactory(instance)
        queues = factory.get()
    elif isinstance(instance, CreditLimit):
        queues = CreditLimitService().get_credit_limit_approval_path(
            instance, kwargs.get("row")
        )
    else:
        queues = ApprovalUser().get_path_for(instance.system, instance.process)

    _remove_existing_queues()
    _create_queues()
    _send_to_next_stage()
    return instance


@receiver(post_delete, sender=PartyAttachment)
def handle_party_delete_postwork(sender, instance, **kwargs):
    MediaRemover.remove_media(sender, instance, **kwargs)


@receiver(post_delete, sender=ShipLocation)
def handle_ship_location_delete_postwork(sender, instance: ShipLocation, **kwargs):
    MediaRemover.remove_media(sender, instance, **kwargs)


@receiver(post_delete, sender=CreditLimit)
def handle_credit_limit_delete_postwork(sender, instance: CreditLimit, **kwargs):
    MediaRemover.remove_media(sender, instance, **kwargs)


@receiver(post_save, sender=Party)
def create_approval_queue_for_pms_new_registration(sender, instance: Party, **kwargs):
    if has_submitted(instance):
        generate_approval_chain(instance)


@receiver(post_save, sender=ShipLocation)
def create_approval_queue_for_pms_ship_location(
    sender, instance: ShipLocation, **kwargs
):
    if has_submitted(instance):
        generate_approval_chain(instance)


@receiver(post_save, sender=CreditLimit)
def create_approval_queue_for_pms_credit_limit_application(
    sender, instance: CreditLimit, **kwargs
):
    if has_submitted(instance):
        instance.status = StatusChoices.PROCESSING
        if not instance.ebs_info_pulled:
            from .tasks import run_credit_limit_post_process

            run_credit_limit_post_process.delay(crl_id=instance.id)
        instance.save()
