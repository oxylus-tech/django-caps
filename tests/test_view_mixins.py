import pytest
from django.test import RequestFactory

import caps.views.mixins as mixins
from caps.models import Agent

factory = RequestFactory()


@pytest.fixture
def agent(db):
    agent = Agent()
    agent.save()
    return agent


@pytest.fixture
def objects(db):
    pass


@pytest.fixture
def object_mixin(rf, agent):
    request = rf.get("/test")
    setattr(request, "agent", agent)
    mixin = mixins.ObjectMixin()
    mixin.request = request
    return mixin


class TestObjectMixin:
    def test_get_agents(self, object_mixin, agent):
        assert object_mixin.get_agents() is agent
