import pytest
import unittest

from django.contrib.auth.models import Group, User, Permission
from django.test import RequestFactory

from caps.models import Agent, CapabilitySet
from .app.models import Capability, ConcreteObject, Reference


__all__ = ("assertCountEqual",)


test_case = unittest.TestCase()
assertCountEqual = test_case.assertCountEqual


req_factory = RequestFactory()


def init_request(req, agent, agents):
    """Initialize request."""
    setattr(req, "agent", agent)
    setattr(req, "agents", agents)
    return req


# -- Agent
@pytest.fixture
def user_group(db):
    return Group.objects.create(name="group-1")


@pytest.fixture
def group(db):
    return Group.objects.create(name="group-2")


@pytest.fixture
def groups(db, user_group, group):
    return [user_group, group]


@pytest.fixture
def user(db, user_group):
    user = User.objects.create_user(username="test_1", password="none")
    user.groups.add(user_group)
    return user


@pytest.fixture
def user_agent(db, user):
    return Agent.objects.create(user=user)


@pytest.fixture
def group_agent(db, user_group):
    return Agent.objects.create(group=user_group)


@pytest.fixture
def user_agents(db, user_agent, group_agent):
    return [user_agent, group_agent]


@pytest.fixture
def agents(db, user_agents, group):
    return user_agents + [Agent.objects.create(group=group)]


# -- Capabilities
@pytest.fixture
def permissions():
    return Permission.objects.all()[0:3]


@pytest.fixture
def permissions_id(permissions):
    return [p.id for p in permissions]


@pytest.fixture
def perm(permissions):
    return permissions[0]


@pytest.fixture
def orphan_perm():
    return Permission.objects.all().last()


@pytest.fixture
def orphan_cap(orphan_perm):
    return Capability.objects.create(permission=orphan_perm, max_derive=1)


@pytest.fixture
def caps_3(permissions):
    caps = [Capability(permission=perm, max_derive=2) for i, perm in enumerate(permissions)]
    Capability.objects.bulk_create(caps)
    return caps


@pytest.fixture
def caps_2(caps_3):
    return [c.derive() for c in caps_3]


@pytest.fixture
def caps_set_3(caps_3):
    obj = CapabilitySet()
    obj.Capability = Capability
    obj.capabilities = caps_3
    return obj


@pytest.fixture
def caps_set_2(caps_2):
    obj = CapabilitySet()
    obj.Capability = Capability
    obj.capabilities = caps_2
    return obj


# -- Objects
@pytest.fixture
def object(db):
    return ConcreteObject.objects.create(name="test-object")


@pytest.fixture
def objects(db):
    objects = [ConcreteObject(name=f"object-{i}") for i in range(0, 3)]
    ConcreteObject.objects.bulk_create(objects)
    return objects


@pytest.fixture
def ref(user_agent, object, caps_3):
    return Reference.create_root(user_agent, object)


@pytest.fixture
def refs_3(agents, objects, caps_3):
    # caps_3: all action, derive 3
    return [Reference.create_root(agents[i], objects[i]) for i in range(0, len(agents))]


@pytest.fixture
def ref_3(refs_3):
    return refs_3[0]


@pytest.fixture
def refs_2(refs_3, agents, permissions_id):
    return [
        refs_3[0].derive(agents[1], permissions_id),
        refs_3[1].derive(agents[2], permissions_id),
        refs_3[2].derive(agents[0], permissions_id),
    ]


@pytest.fixture
def refs(refs_3, refs_2):
    return refs_3 + refs_2
