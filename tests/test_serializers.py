from uuid import uuid4

import pytest
from rest_framework.serializers import ValidationError

from caps import serializers
from .app.models import Capability, ConcreteObject


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
def derive_field():
    return serializers.DeriveCapField()


class TestDeriveCapField:
    def test_to_representation_with_tuple(self, derive_field):
        assert derive_field.to_representation([1, "2"]) == [1, 2]

    def test_to_representation_with_tuple_invalid(self, derive_field):
        with pytest.raises(ValueError):
            derive_field.to_representation([1, "2mlk"])

    @pytest.mark.django_db(transaction=True)
    def test_to_representation_with_capability(self, derive_field, perm):
        cap = Capability(permission=perm, max_derive=2)
        assert derive_field.to_representation(cap) == [cap.permission_id, cap.max_derive]

    def test_to_representation_with_int(self, derive_field):
        assert derive_field.to_representation(123) == [123, None]

    def test_to_representation_raises_valueerror(self, derive_field):
        with pytest.raises(ValueError):
            derive_field.to_representation("123")

    def test_to_internal_value_with_tuple(self, derive_field):
        assert derive_field.to_internal_value(["12", 13]) == [12, 13]

    def test_to_internal_value_with_wrong_tuple(self, derive_field):
        with pytest.raises(ValidationError):
            derive_field.to_internal_value([1, 2, 3])

    def test_to_internal_value_with_int(self, derive_field):
        assert derive_field.to_internal_value("12") == [12, None]
        assert derive_field.to_internal_value(12) == [12, None]

    def test_to_internal_value_raises_valueerror(self, derive_field):
        with pytest.raises(ValidationError):
            derive_field.to_internal_value("--")


@pytest.fixture
def derive_serializer():
    return serializers.DeriveSerializer()


class TestDeriveSerializer:
    def test_validate_receiver(self, derive_serializer, user_agent):
        assert derive_serializer.validate_receiver(user_agent.uuid) == user_agent

    def test_validate_receiver_with_invalid_receiver(self, derive_serializer, user_agent):
        with pytest.raises(ValidationError):
            derive_serializer.validate_receiver(uuid4())
