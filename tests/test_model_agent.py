import pytest
from django.core.exceptions import ValidationError

from caps.models import Agent

__all__ = ("TestAgentQuerySet", "TestAgent")


# TODO:
# - test anonymous users on QuerySet
@pytest.mark.django_db(transaction=True)
class TestAgentQuerySet:
    def test_user_anonymous(self):
        pass

    def test_user_strict(self, user, user_agents):
        query = Agent.objects.user(user, strict=True)
        assert len(query) == 1
        assert query[0].user == user

    def test_user(self, user, user_group, user_agents):
        query = Agent.objects.user(user)
        assert len(query) == len(user_agents)
        assert all(a.user == user or a.group == user_group for a in query)

    def test_group(self, agents, groups):
        for group in groups:
            queryset = Agent.objects.group(group)
            assert queryset.count() == 1
            assert group == next(iter(queryset)).group


@pytest.mark.django_db(transaction=True)
class TestAgent:
    def test_is_anonymous_return_true(self):
        agent = Agent()
        assert agent.is_anonymous

    def test_is_anonymous_return_false(self, agents):
        for agent in agents:
            assert not agent.is_anonymous

    def test_clean_raises_on_user_and_group(self, user, groups):
        agent = Agent(user=user, group=groups[0])
        with pytest.raises(ValidationError):
            agent.clean()

    def test_clean_raises_on_is_default_not_allowed(self, groups):
        agent = Agent(group=groups[0], is_default=True)
        with pytest.raises(ValidationError):
            agent.clean()

    def test_clean_anonymous_is_default(self):
        agent = Agent()
        agent.clean()
