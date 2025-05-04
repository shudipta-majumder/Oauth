from rest_framework.serializers import ModelSerializer

from ..models import Contact

__all__ = ["ContactSerializer"]


class ContactSerializer(ModelSerializer):
    def to_representation(self, instance: Contact):
        response = super().to_representation(instance)
        request = self.context.get("request")

        if request:
            # Get the URI for the attachment field without the domain
            if instance.pp_photo_file:
                pp_photo_file_url = instance.pp_photo_file.url
                domain = request.build_absolute_uri("/")[:-1]
                response["pp_photo_file"] = pp_photo_file_url.replace(domain, "")
            if instance.nid_file:
                nid_file_url = instance.nid_file.url
                domain = request.build_absolute_uri("/")[:-1]
                response["nid_file"] = nid_file_url.replace(domain, "")
            if instance.vcard_file:
                vcard_file_url = instance.vcard_file.url
                domain = request.build_absolute_uri("/")[:-1]
                response["vcard_file"] = vcard_file_url.replace(domain, "")
            if instance.ecard_file:
                ecard_file_url = instance.ecard_file.url
                domain = request.build_absolute_uri("/")[:-1]
                response["ecard_file"] = ecard_file_url.replace(domain, "")

        return response

    class Meta:
        model = Contact
        fields = "__all__"
