from rest_framework import serializers
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

    class Meta:
        fields = ["uuid", "origin_id", "depth", "receiver_id", "expiration"]


class ObjectSerializer(serializers.Serializer):
    """
    Base serializer for Objects. It provides :py:attr:`uuid` field.
    """

    uuid = serializers.UUIDField(source="reference.uuid", read_only=True)
    """ Reference uuid. """

    class Meta:
        fields = ["uuid"]
