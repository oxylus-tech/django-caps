from uuid import uuid4

import pytest
from rest_framework.serializers import ValidationError

from caps import serializers
from .conftest import api_req_factory, init_api_request
from .app.models import ConcreteOwned


class ConcreteOwnedSerializer(serializers.OwnedSerializer):
    class Meta:
        fields = "__all__"
        model = ConcreteOwned


@pytest.fixture
def req(user):
    return init_api_request(api_req_factory.post("/test", {}), user)


@pytest.fixture
def object_ser(user_agent, user_agents):
    return ConcreteOwnedSerializer(object, context={"agent": user_agent, "agents": user_agents})


class TestOwnedSerializer:
    def test__init__(self, object):
        ser = ConcreteOwnedSerializer(object)
        assert "pk" not in ser.data
        assert "uuid" not in ser.data
        assert "access" in ser.data

    def test_deserialize(self, req, user_agent, user_agents):
        ser = ConcreteOwnedSerializer(
            data={"name": "name", "owner": user_agent.uuid}, context={"agent": user_agent, "agents": user_agents}
        )
        assert ser.is_valid(raise_exception=True)
        # assert ser.validated_data ==

    def test_validate_without_request_agent(self, object_ser, user_agent):
        assert object_ser.validate({"name": "name"})["owner"] == user_agent

    def test_validate_owner_with_request_agent(self, object_ser, user_agent):
        assert object_ser.validate_owner(user_agent) == user_agent

    def test_validate_owner_with_other_request_agent(self, object_ser, group_agent):
        assert object_ser.validate_owner(group_agent) == group_agent

    def test_validate_owner_raises_invalid_owner(self, object_ser, user_2_agent):
        with pytest.raises(ValidationError):
            object_ser.validate_owner(user_2_agent.uuid)


@pytest.fixture
def share_serializer():
    return serializers.ShareSerializer()


class TestShareSerializer:
    def test_validate_receiver(self, share_serializer, user_agent):
        assert share_serializer.validate_receiver(user_agent.uuid) == user_agent

    def test_validate_receiver_with_invalid_receiver(self, share_serializer, user_agent):
        with pytest.raises(ValidationError):
            share_serializer.validate_receiver(uuid4())
