from rest_framework.serializers import CharField, Serializer

__all__ = ["WITPSerializer"]


class WITPSerializer(Serializer):
    witp_code = CharField(required=True, allow_null=False, max_length=40)
