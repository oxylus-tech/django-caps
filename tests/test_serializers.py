from uuid import uuid4

import pytest
from rest_framework.serializers import ValidationError

from caps import serializers
from .app.models import ConcreteObject


class ConcreteObjectSerializer(serializers.ObjectSerializer):
    class Meta:
        fields = "__all__"
        model = ConcreteObject


class TestObjectSerializer:
    def test__init__(self, object):
        ser = ConcreteObjectSerializer(object)
        assert "pk" not in ser.data
        assert "id" not in ser.data
        assert "reference" in ser.data


@pytest.fixture
def cap_field():
    return serializers.CapabilityField()


class TestRawCapabilityField:
    def test_to_representation(self, cap_field, caps_3):
        cap = caps_3[0]
        assert cap_field.to_representation(cap) == cap.serialize()

    def test_to_internal_value_with_tuple(self, cap_field, caps_3):
        cap = caps_3[0]
        assert cap_field.to_internal_value(cap.serialize()) == cap


@pytest.fixture
def derive_serializer():
    return serializers.DeriveSerializer()


class TestDeriveSerializer:
    def test_validate_receiver(self, derive_serializer, user_agent):
        assert derive_serializer.validate_receiver(user_agent.uuid) == user_agent

    def test_validate_receiver_with_invalid_receiver(self, derive_serializer, user_agent):
        with pytest.raises(ValidationError):
            derive_serializer.validate_receiver(uuid4())
