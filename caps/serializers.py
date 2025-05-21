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

    origin = serializers.SerializerMethodField(source="get_origin")

    class Meta:
        fields = ["uuid", "origin", "depth", "emitter", "receiver", "expiration"]
        read_only_fields = "__all__"

    def get_origin(self, obj):
        return obj.origin.uuid


class ObjectSerializer(serializers.ModelSerializer):
    """
    Base serializer for Objects. It provides :py:attr:`uuid` field.
    """

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


class CapabilityField(serializers.Field):
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
