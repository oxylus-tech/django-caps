import pytest
import unittest

from django.contrib.auth.models import Group, User

from caps.models import Agent, Capability, CapabilitySet
from .app.models import ConcreteObject, ConcreteReference


__all__ = ("assertCountEqual",)


test_case = unittest.TestCase()
assertCountEqual = test_case.assertCountEqual


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
def user_agents(db, user, user_group):
    return [Agent.objects.create(user=user), Agent.objects.create(group=user_group)]


@pytest.fixture
def agents(db, user_agents, group):
    return user_agents + [Agent.objects.create(group=group)]


# -- Capabilities
@pytest.fixture
def caps_names():
    return ["action_1", "action_2", "action_3"]


@pytest.fixture
def orphan_cap():
    return Capability.objects.create(name="orphan", max_derive=1)

@pytest.fixture
def caps_3(caps_names):
    caps = [Capability(name=name, max_derive=2) for i, name in enumerate(caps_names)]
    Capability.objects.bulk_create(caps)
    return caps


@pytest.fixture
def caps_2(caps_3):
    return [c.derive() for c in caps_3]


@pytest.fixture
def caps_1(caps_2):
    return [c.derive() for c in caps_2]


@pytest.fixture
def caps_set_3(caps_3):
    return CapabilitySet(caps_3)


@pytest.fixture
def caps_set_2(caps_2):
    return CapabilitySet(caps_2)


@pytest.fixture
def caps_set_1(caps_1):
    return CapabilitySet(caps_1)


# -- Objects
@pytest.fixture
def objects(db):
    objects = [ConcreteObject(name=f"object-{i}") for i in range(0, 3)]
    ConcreteObject.objects.bulk_create(objects)
    return objects


@pytest.fixture
def refs_3(agents, objects, caps_3):
    # caps_3: all action, derive 3
    return [ConcreteReference.create(agents[i], objects[i], caps_3) for i in range(0, len(agents))]


@pytest.fixture
def refs_2(refs_3, agents, caps_2):
    # caps_2: all actions, derive 2
    # FIXME: TestReference.test_create
    return [
        refs_3[0].derive(agents[1], caps_2),
        refs_3[1].derive(agents[2], caps_2),
        refs_3[2].derive(agents[0], caps_2),
    ]


@pytest.fixture
def refs_1(refs_2, agents):
    return [
        refs_2[0].derive(agents[2]),
        refs_2[1].derive(agents[0]),
        refs_2[2].derive(agents[1]),
    ]


@pytest.fixture
def refs(refs_3, refs_2, refs_1):
    return refs_3 + refs_2 + refs_1
