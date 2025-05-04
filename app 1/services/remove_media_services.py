from logging import getLogger

from django.core.files.storage import default_storage
from django.db import models

_logger = getLogger(__name__)


class MediaRemover:
    @staticmethod
    def remove_media(sender, instance, **kwargs):
        if hasattr(instance, "_meta"):  # Check if instance is a model instance
            for field in instance._meta.fields:
                if isinstance(field, (models.FileField, models.ImageField)):
                    file_field_value = getattr(instance, field.name, None)

                    if file_field_value and isinstance(
                        file_field_value, models.fields.files.FieldFile
                    ):
                        file_path = file_field_value.path
                        default_storage.delete(file_path)
                        _logger.info(
                            f"An attachment for {instance!r} ID({instance.pk!r}) has been removed from disk."
                        )
