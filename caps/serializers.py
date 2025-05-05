from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from . import models
from .models import Cap


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

    origin = serializers.SerializerMethodField(source="get_origin")
    capabilities = CapabilitySerializer(many=True, read_only=True)

    class Meta:
        fields = ["uuid", "origin", "depth", "emitter", "receiver", "expiration"]
        read_only_fields = ["uuid", "depth", "emitter", "receiver", "expiration"]

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


class DeriveCapField(serializers.Field):
    """Serialize/Deserialize a :py:type:`~caps.models.capability_set.Cap`, used to derive a reference.

    Allowed values are:

        - a tuple of ``(permission_id, max_derive|None)``
        - an integer value for ``permission_id``
        - (serializing) a Capability

    """

    def to_representation(self, value: Cap | models.Capability) -> list[int, int | None]:
        if isinstance(value, (tuple, list)):
            return [int(value[0]), int(value[1])]
        elif isinstance(value, models.Capability):
            return [value.permission_id, value.max_derive]
        elif isinstance(value, int):
            return [value, None]
        raise ValueError(f"Invalid value type for Cap: {value}")

    def to_internal_value(self, value: Cap) -> list[int, int | None]:
        if isinstance(value, (tuple, list)):
            if len(value) != 2:
                raise ValidationError("Incorrect length for list or tuple (must be 2: permission id, max derive)")
            return [int(value[0]), int(value[1]) if value is not None else None]
        try:
            return [int(value), None]
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
        try:
            return models.Agent.objects.get(uuid=value)
        except ObjectDoesNotExist:
            raise ValidationError("Invalid receiver.")
