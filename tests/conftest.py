import pytest
import unittest

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, User, Permission
from django.test import RequestFactory

from caps.models import Agent, Capability, CapabilitySet
from .app.models import ConcreteObject, Reference


__all__ = ("assertCountEqual",)


test_case = unittest.TestCase()
assertCountEqual = test_case.assertCountEqual


req_factory = RequestFactory()


def init_request(req, agent, agents):
    """Initialize request."""
    setattr(req, "user", agent.user)
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
def user_perms(user):
    ct = ContentType.objects.get_for_model(ConcreteObject)
    perms = Permission.objects.filter(content_type=ct)
    user.user_permissions.set(perms)
    return perms


@pytest.fixture
def user_2(db):
    return User.objects.create_user(username="test_2", password="none-2")


@pytest.fixture
def user_2_perms(user_2):
    ct = ContentType.objects.get_for_model(ConcreteObject)
    perms = Permission.objects.filter(content_type=ct, codename__contains="view")
    user_2.user_permissions.set(perms)
    return perms


@pytest.fixture
def anon_agent(db, user):
    return Agent.objects.create()


@pytest.fixture
def user_agent(db, user):
    return Agent.objects.create(user=user, is_default=True)


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
def permissions(db):
    perms = Permission.objects.all().values_list("content_type__app_label", "codename")[0:3]
    return [".".join(p) for p in perms]


@pytest.fixture
def perm(permissions):
    return permissions[0]


@pytest.fixture
def orphan_perm():
    return Permission.objects.all().last().codename


@pytest.fixture
def orphan_cap(orphan_perm):
    return Capability(permission=orphan_perm, max_derive=1)


@pytest.fixture
def caps_3(permissions):
    caps = [Capability(permission=perm, max_derive=2) for i, perm in enumerate(permissions)]
    ConcreteObject.root_reference_grants = {
        **dict(c.serialize() for c in caps),
        "caps_test.view_concreteobject": 1,
    }
    return caps


@pytest.fixture
def caps_2(caps_3):
    return [c.derive() for c in caps_3]


@pytest.fixture
def caps_set_3(caps_3):
    obj = CapabilitySet()
    obj.capabilities = caps_3
    return obj


@pytest.fixture
def caps_set_2(caps_2):
    obj = CapabilitySet()
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
    # FIXME: set object.reference to ref
    return Reference.create_root(user_agent, object)


@pytest.fixture
def group_ref(group_agent, object, caps_3):
    return Reference.create_root(group_agent, object)


@pytest.fixture
def refs_3(agents, objects, caps_3):
    # caps_3: all action, derive 3
    # We enforce the values
    return [Reference.create_root(agents[i], objects[i]) for i in range(0, len(agents))]


@pytest.fixture
def ref_3(refs_3):
    return refs_3[0]


# FIXME
@pytest.fixture
def refs_2(refs_3, agents, caps_2):
    return [
        refs_3[0].derive(agents[1], caps_2),
        refs_3[1].derive(agents[2], caps_2),
        refs_3[2].derive(agents[0], caps_2),
    ]


@pytest.fixture
def refs(refs_3, refs_2):
    return refs_3 + refs_2
