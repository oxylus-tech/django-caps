"""
This module provides serializer (and base serializers) for Django-Caps' models.

** Note: we never expose internal db id to the external world as they are predictable
for an attacker. Instead we refer to them using their UUID. **
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from django.utils.translation import gettext_lazy as _

from . import models


__all__ = ("AgentSerializer", "AccessSerializer", "OwnedSerializer", "ShareSerializer")


class UUIDSerializer(serializers.Serializer):
    """Serialize uuids as id."""

    id = serializers.UUIDField(source="uuid", read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "pk" in self.fields:
            del self.fields["pk"]
        if "uuid" in self.fields:
            del self.fields["uuid"]


class AgentSerializer(UUIDSerializer, serializers.ModelSerializer):
    """Serializer for :py:class:`~caps.models.agent.Agent`."""

    name = serializers.SerializerMethodField()
    """ Provided fields for utility """

    class Meta:
        model = models.Agent
        fields = ["id", "user", "group", "name"]

    def get_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        if obj.group:
            return obj.group.name
        return _("Anonymous")


class AccessSerializer(UUIDSerializer, serializers.Serializer):
    """
    Serializer for :py:class:`~.models.capability.Access`.

    Implemented as simple Serializer, since the corresponding models are generated based on
    concrete :py:class:`.models.object.Owned`.
    """

    emitter = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    expiration = serializers.DateTimeField()
    grants = serializers.JSONField()

    class Meta:
        fields = ["id", "origin", "emitter", "receiver", "expiration", "grants"]
        read_only_fields = fields

    def get_emitter(self, obj):
        return obj.emitter and str(obj.emitter.uuid) or None

    def get_receiver(self, obj):
        return obj.receiver and str(obj.receiver.uuid) or None

    def get_origin(self, obj):
        return obj.origin and str(obj.origin.uuid) or None


class OwnedSerializer(UUIDSerializer, serializers.ModelSerializer):
    """
    Base serializer for :py:class:`~.models.owned.Owned`.

    When the owned object has ``access`` set, it will use the access' uuid
    as id. This happens for example when it is fetched from database using
    the :py:meth:`~.models.owned.OwnedQuerySet.access` method.

    It is highly recommanded to set the user's ``agent`` and ``agents``
    in the serializer context (implemented API view already does it for you). This
    allows validation of the owner.
    """

    id = serializers.SerializerMethodField()
    owner = serializers.SlugRelatedField(
        slug_field="uuid", allow_null=True, required=False, queryset=models.Agent.objects.all()
    )
    access = AccessSerializer(read_only=True)
    """ Access """
    path = serializers.CharField(required=False, allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        agent = self.context.get("agent")
        agents = self.context.get("agents")
        if (agent and not agents) or (not agent and agents):
            raise ValueError("Provide both or none of context `agent` and `agents`.")
        if agents and agent not in agents:
            raise ValueError("Context `agents` does not includes `agent`.")

    def get_id(self, obj):
        """Get uuid from ``obj.access`` if present."""
        if obj.access:
            return str(obj.access.uuid)
        return str(obj.uuid)

    def validate(self, data):
        v_data = super().validate(data)
        if agent := self.context.get("agent"):
            if not v_data.get("owner"):
                v_data["owner"] = agent
        if "path" in v_data:
            del v_data["path"]

        return v_data

    def validate_owner(self, value: models.Agent):
        # value is an Agent, as the field is a SlugRelatedField.
        if not value:
            if agent := self.context.get("agent"):
                return agent
        elif agents := self.context.get("agents"):
            if value == self.context["agent"] or value in agents:
                return value
        raise ValidationError("Invalid owner")

    class Meta:
        fields = ["access"]
        read_only_fields = [
            "access",
            "uuid",
        ]


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
