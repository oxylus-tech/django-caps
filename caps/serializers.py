from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from . import models


__all__ = ("AgentSerializer", "AccessSerializer", "ObjectSerializer", "ShareSerializer")


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for :py:class:`caps.models.agent.Agent`."""

    class Meta:
        model = models.Agent
        fields = ["user_id", "group_id"]


class AccessSerializer(serializers.Serializer):
    """
    Serializer for :py:class:`caps.models.capability.Access`.

    Implemented as simple Serializer, since the corresponding models are generated based on
    concrete :py:class:`.models.object.Object`.
    """

    uuid = serializers.CharField(read_only=True)
    emitter = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    expiration = serializers.DateTimeField()
    grants = serializers.JSONField()

    class Meta:
        fields = ["uuid", "origin", "emitter", "receiver", "expiration", "grants"]
        read_only_fields = fields

    def get_emitter(self, obj):
        return obj.emitter and str(obj.emitter.uuid) or None

    def get_receiver(self, obj):
        return obj.receiver and str(obj.receiver.uuid) or None

    def get_origin(self, obj):
        return obj.origin and str(obj.origin.uuid) or None


class ObjectSerializer(serializers.ModelSerializer):
    """
    Base serializer for Objects. It provides :py:attr:`uuid` field.
    """

    uuid = serializers.SerializerMethodField()
    owner = serializers.UUIDField(source="owner__uuid", read_only=True)
    access = AccessSerializer(read_only=True)
    """ Access """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "pk" in self.fields:
            del self.fields["pk"]
        if "id" in self.fields:
            del self.fields["id"]

    def get_uuid(self, obj):
        if obj.access:
            return str(obj.access.uuid)
        return str(obj.uuid)

    def validate(self, data):
        v_data = super().validate(data)
        if request := self.context.get("request"):
            v_data["owner"] = request.agent
        return v_data

    class Meta:
        fields = ["access"]
        read_only_fields = ["access", "uuid", "owner"]


class ShareSerializer(serializers.Serializer):
    """
    This serializer is used to deserialize requests to
    derive a Access (:py:meth:`~caps.views.api.AccessViewSet.share`).
    """

    receiver = serializers.UUIDField()
    expiration = serializers.DateTimeField(required=False)
    grants = serializers.DictField(child=serializers.IntegerField())

    def validate_receiver(self, value):
        try:
            return models.Agent.objects.get(uuid=value)
        except ObjectDoesNotExist:
            raise ValidationError("Invalid receiver.")
