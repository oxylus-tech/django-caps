import pytest

from django.contrib.auth.models import AnonymousUser
from caps.models import Agent
from caps.middleware import AgentMiddleware
from .conftest import req_factory, assertCountEqual


@pytest.fixture
def middleware():
    return AgentMiddleware(lambda r: None)


@pytest.fixture
def req(user):
    req = req_factory.get("/")
    req.user = user
    return req


class TestAgentMiddleware:
    def test__call__(self, middleware, req, user, user_agent, user_agents):
        middleware(req)
        assert req.agent == user_agent
        assertCountEqual(req.agents, user_agents)

    def test_get_agents(self, middleware, req, user_agents):
        agents = middleware.get_agents(req)
        assert agents[0].user_id == req.user.id
        assertCountEqual(agents, user_agents)

    def test_get_agent_with_anonymous_user(self, middleware, req, anon_agent):
        req.user = AnonymousUser()
        agents = Agent.objects.filter(id=anon_agent.id)
        assert middleware.get_agent(req, agents) == anon_agent

    def test_get_agent_with_existing_one(self, middleware, req, user_agents, user_agent):
        assert middleware.get_agent(req, user_agents) == user_agent

    def test_get_agent_create_new_one(self, middleware, req):
        agent = middleware.get_agent(req, [])
        assert agent.user == req.user
        assert req.user.agent == agent
