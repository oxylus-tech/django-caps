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
def share_serializer():
    return serializers.ShareSerializer()


class TestShareSerializer:
    def test_validate_receiver(self, share_serializer, user_agent):
        assert share_serializer.validate_receiver(user_agent.uuid) == user_agent

    def test_validate_receiver_with_invalid_receiver(self, share_serializer, user_agent):
        with pytest.raises(ValidationError):
            share_serializer.validate_receiver(uuid4())
