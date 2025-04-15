from rest_framework import serializers
from rest_framework.serializers import ValidationError

from . import models

__all__ = ("AgentSerializer", "CapabilitySerializer", "ReferenceSerializer", "ObjectSerializer")


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for :py:class:`caps.models.agent.Agent`."""

    class Meta:
        model = models.Agent
        fields = ["user_id", "group_id"]


class CapabilitySerializer(serializers.Serializer):
    """
    Serializer for :py:class:`caps.models.capability.Capability`.

    Implemented as simple Serializer, since the corresponding models are generated based on
    concrete :py:class:`.models.object.Object`.
    """

    class Meta:
        fields = ["permission_id", "reference_id", "max_derive"]


class ReferenceSerializer(serializers.Serializer):
    """
    Serializer for :py:class:`caps.models.capability.Reference`.

    Implemented as simple Serializer, since the corresponding models are generated based on
    concrete :py:class:`.models.object.Object`.
    """

    origin = serializers.UUIDField(source="origin__uuid")
    capabilities = CapabilitySerializer(many=True, read_only=True)

    class Meta:
        fields = ["uuid", "origin", "depth", "emitter", "receiver", "expiration"]
        read_only_fields = ["uuid", "depth", "emitter", "receiver", "expiration"]


class ObjectSerializer(serializers.Serializer):
    """
    Base serializer for Objects. It provides :py:attr:`uuid` field.
    """

    reference = ReferenceSerializer(read_only=True)
    """ Reference """

    class Meta:
        fields = ["reference"]


class DeriveCapField(serializers.Field):
    """Serialize/Deserialize a :py:type:`~caps.models.capability_set.Cap`, used to derive a reference.

    Allowed values are:

        - a tuple of ``(permission_id, max_derive|None)``
        - an integer value for ``permission_id``
        - (serializing) a Capability

    """

    def to_representation(self, value):
        if isinstance(value, (tuple, list)):
            return [int(value[0]), int(value[1])]
        elif isinstance(value, models.Capability):
            return [value.permission_id, value.max_derive]
        elif isinstance(value, int):
            return value
        raise ValueError(f"Invalid value type for Cap: {value}")

    def to_internal_value(self, value):
        if isinstance(value, (tuple, list)):
            if len(value) != 2:
                raise ValidationError("Incorrect length for list or tuple (must be 2: permission id, max derive)")
            return [int(value[0]), int(value[1])]
        try:
            return int(value)
        except ValueError:
            raise ValidationError("Provided value must be convertible to an integer")


class DeriveSerializer(serializers.Serializer):
    """
    This serializer is used to deserialize requests to
    derive a Reference (:py:meth:`~caps.views.api.ReferenceViewSet.derive`).
    """

    receiver = serializers.UUIDField()
    caps = serializers.ListField(child=DeriveCapField())

    def validate_receiver(self, value):
        return models.Agent.objects.get(uuid=value)
