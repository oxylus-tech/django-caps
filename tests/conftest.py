import pytest
import unittest

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, User, Permission
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate

from caps.models import Agent
from .app.models import ConcreteOwned


__all__ = ("assertCountEqual",)


test_case = unittest.TestCase()
assertCountEqual = test_case.assertCountEqual


req_factory = RequestFactory()
api_req_factory = APIRequestFactory()


def init_request(req, user):
    """Initialize request."""
    setattr(req, "user", user)
    return req


def init_api_request(req, user):
    """Initialize request."""
    setattr(req, "user", user)
    req.authenticators = None
    force_authenticate(req, user=user)
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
def user_admin(db, user_group):
    return User.objects.create_user(username="admin", password="none-3", is_superuser=True)


@pytest.fixture
def user_perms(user):
    ct = ContentType.objects.get_for_model(ConcreteOwned)
    perms = Permission.objects.filter(content_type=ct)
    user.user_permissions.set(perms)
    return perms


@pytest.fixture
def user_2(db, user_group):
    user = User.objects.create_user(username="test_2", password="none-2")
    user.groups.add(user_group)
    return user


@pytest.fixture
def user_3(db, user_group):
    user = User.objects.create_user(username="test_3", password="none-3")
    user.groups.add(user_group)
    return user


@pytest.fixture
def user_2_perms(user_2):
    ct = ContentType.objects.get_for_model(ConcreteOwned)
    perms = Permission.objects.filter(content_type=ct, codename__contains="view")
    user_2.user_permissions.set(perms)
    return perms


@pytest.fixture
def anon_agent(db, user):
    return Agent.objects.create()


@pytest.fixture
def user_agent(db, user):
    return user.agent


@pytest.fixture
def user_2_agent(db, user_2):
    return user_2.agent


@pytest.fixture
def group_agent(db, user_group):
    return user_group.agent


@pytest.fixture
def user_agents(db, user_agent, group_agent):
    return [user_agent, group_agent]


@pytest.fixture
def user_2_agents(db, user_2_agent, group_agent):
    return [user_2_agent, group_agent]


@pytest.fixture
def agents(db, user_2_agents, group):
    return user_2_agents + [group.agent]


# -- Capabilities
@pytest.fixture
def permissions(db):
    perms = Permission.objects.all().values_list("content_type__app_label", "codename")[0:3]
    perms = [".".join(p) for p in perms]

    if perms[0] not in ConcreteOwned.root_grants:
        ConcreteOwned.root_grants.update({p: 2 for p in perms})
    return perms


@pytest.fixture
def perm(permissions):
    return permissions[0]


@pytest.fixture
def orphan_perm():
    return Permission.objects.all().last().codename


# -- Owneds
@pytest.fixture
def object(user_agent, db):
    return ConcreteOwned.objects.create(name="test-object", owner=user_agent)


@pytest.fixture
def objects(user_agent, db):
    objects = [ConcreteOwned(name=f"object-{i}", owner=user_agent) for i in range(0, 3)]
    ConcreteOwned.objects.bulk_create(objects)
    return objects


@pytest.fixture
def user_2_object(user_2_agent, db):
    return ConcreteOwned.objects.create(name="user-2-object", owner=user_2_agent)


@pytest.fixture
def access(user_2_agent, object):
    # FIXME: set object.access to access
    return object.share(user_2_agent)


@pytest.fixture
def group_access(group_agent, object):
    return object.share(group_agent, object)


@pytest.fixture
def accesses_3(agents, objects):
    # caps_3: all action, derive 3
    # We enforce the values
    return [object.share(agent) for object, agent in zip(objects, agents)]


@pytest.fixture
def access_3(accesses_3):
    return accesses_3[0]


# FIXME
@pytest.fixture
def accesses_2(accesses_3, agents):
    return [
        accesses_3[0].share(agents[1]),
        accesses_3[1].share(agents[2]),
        accesses_3[2].share(agents[0]),
    ]


@pytest.fixture
def accesses(accesses_3, accesses_2):
    return accesses_3 + accesses_2
