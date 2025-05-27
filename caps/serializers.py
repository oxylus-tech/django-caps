from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from . import models
from .models.capability import RawCapability


__all__ = ("AgentSerializer", "ReferenceSerializer", "ObjectSerializer", "CapabilityField", "DeriveSerializer")


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for :py:class:`caps.models.agent.Agent`."""

    class Meta:
        model = models.Agent
        fields = ["user_id", "group_id"]


class ReferenceSerializer(serializers.Serializer):
    """
    Serializer for :py:class:`caps.models.capability.Reference`.

    Implemented as simple Serializer, since the corresponding models are generated based on
    concrete :py:class:`.models.object.Object`.
    """

    uuid = serializers.CharField()
    depth = serializers.IntegerField()
    emitter = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    expiration = serializers.DateTimeField()
    grants = serializers.JSONField()

    class Meta:
        fields = ["uuid", "origin", "depth", "emitter", "receiver", "expiration", "grants"]
        read_only_fields = "__all__"

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

    uuid = serializers.CharField(source="reference__uuid", read_only=True)
    """ Reference UUID """
    reference = ReferenceSerializer(read_only=True)
    """ Reference """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "pk" in self.fields:
            del self.fields["pk"]
        if "id" in self.fields:
            del self.fields["id"]

    class Meta:
        fields = ["reference"]
        read_only_fields = ["reference", "uuid"]


class CapabilityField(serializers.JSONField):
    """Serialize/Deserialize a :py:type:`~caps.models.capability_set.Cap`, used to derive a reference.

    Allowed values are:

        - a tuple of ``(permission_id, max_derive|None)``
        - an integer value for ``permission_id``
        - (serializing) a Capability

    """

    capability_class = models.Capability

    def to_representation(self, value: models.Capability) -> tuple[str, int]:
        return value.serialize()

    def to_internal_value(self, value: RawCapability) -> list[int, int | None]:
        try:
            if isinstance(value, str):
                value = value.split(",")
                value = [value[0].strip(), value[1] and int(value[1]) or 0]
            return self.capability_class.deserialize(value)
        except ValueError as err:
            raise ValidationError(str(err))


class DeriveSerializer(serializers.Serializer):
    """
    This serializer is used to deserialize requests to
    derive a Reference (:py:meth:`~caps.views.api.ReferenceViewSet.derive`).
    """

    receiver = serializers.UUIDField()
    capabilities = serializers.ListField(child=CapabilityField())

    def validate_receiver(self, value):
        try:
            return models.Agent.objects.get(uuid=value)
        except ObjectDoesNotExist:
            raise ValidationError("Invalid receiver.")
