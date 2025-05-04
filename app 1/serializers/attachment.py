from rest_framework.serializers import ModelSerializer

from ..models import AttachmentRepository, ExtraAttachment, PartyAttachment

__all__ = ["AttachmentSerializer", "AttachmentRepositorySerializer", "ExtraSerializer"]


class AttachmentSerializer(ModelSerializer):
    class Meta:
        model = PartyAttachment
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        if request:
            # Get the URI for the attachment field without the domain
            attachment_uri = instance.attachment.url
            domain = request.build_absolute_uri("/")[:-1]
            representation["attachment"] = attachment_uri.replace(domain, "")

        return representation


class ExtraSerializer(ModelSerializer):
    class Meta:
        model = ExtraAttachment
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")

        if request:
            # Get the URI for the attachment field without the domain
            attachment_uri = instance.file.url
            domain = request.build_absolute_uri("/")[:-1]
            representation["file"] = attachment_uri.replace(domain, "")

        return representation


class AttachmentRepositorySerializer(ModelSerializer):
    class Meta:
        model = AttachmentRepository
        fields = "__all__"
