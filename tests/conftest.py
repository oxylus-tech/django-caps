import pytest
import unittest

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, User, Permission
from django.test import RequestFactory

from caps.models import Agent
from .app.models import ConcreteObject


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
def user_2(db, user_group):
    user = User.objects.create_user(username="test_2", password="none-2")
    user.groups.add(user_group)
    return user


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
def user_2_agent(db, user_2):
    return Agent.objects.create(user=user_2, is_default=True)


@pytest.fixture
def group_agent(db, user_group):
    return Agent.objects.create(group=user_group)


@pytest.fixture
def user_agents(db, user_agent, group_agent):
    return [user_agent, group_agent]


@pytest.fixture
def user_2_agents(db, user_2_agent, group_agent):
    return [user_2_agent, group_agent]


@pytest.fixture
def agents(db, user_2_agents, group):
    return user_2_agents + [Agent.objects.create(group=group)]


# -- Capabilities
@pytest.fixture
def permissions(db):
    perms = Permission.objects.all().values_list("content_type__app_label", "codename")[0:3]
    perms = [".".join(p) for p in perms]

    if perms[0] not in ConcreteObject.root_grants:
        ConcreteObject.root_grants.update({p: 2 for p in perms})
    return perms


@pytest.fixture
def perm(permissions):
    return permissions[0]


@pytest.fixture
def orphan_perm():
    return Permission.objects.all().last().codename


# -- Objects
@pytest.fixture
def object(user_agent, db):
    return ConcreteObject.objects.create(name="test-object", owner=user_agent)


@pytest.fixture
def objects(user_agent, db):
    objects = [ConcreteObject(name=f"object-{i}", owner=user_agent) for i in range(0, 3)]
    ConcreteObject.objects.bulk_create(objects)
    return objects


@pytest.fixture
def user_2_object(user_2_agent, db):
    return ConcreteObject.objects.create(name="user-2-object", owner=user_2_agent)


@pytest.fixture
def ref(user_2_agent, object):
    # FIXME: set object.reference to ref
    return object.share(user_2_agent)


@pytest.fixture
def group_ref(group_agent, object):
    return object.share(group_agent, object)


@pytest.fixture
def refs_3(agents, objects):
    # caps_3: all action, derive 3
    # We enforce the values
    return [object.share(agent) for object, agent in zip(objects, agents)]


@pytest.fixture
def ref_3(refs_3):
    return refs_3[0]


# FIXME
@pytest.fixture
def refs_2(refs_3, agents):
    return [
        refs_3[0].share(agents[1]),
        refs_3[1].share(agents[2]),
        refs_3[2].share(agents[0]),
    ]


@pytest.fixture
def refs(refs_3, refs_2):
    return refs_3 + refs_2
