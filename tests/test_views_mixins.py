from uuid import uuid4

import pytest
from django.http import Http404

from caps.views import mixins
from .conftest import init_request, req_factory
from .app.models import ConcreteObject


class BaseMixin:
    object = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def dispatch(self, request, *args, **kwargs):
        pass

    def get_queryset(self):
        return ConcreteObject.objects.all()

    def get_object(self):
        return self.object


class ObjectMixin(mixins.ObjectMixin, BaseMixin):
    model = ConcreteObject


class ObjectPermissionMixin(mixins.ObjectPermissionMixin, BaseMixin):
    model = ConcreteObject


class SingleObjectMixin(mixins.SingleObjectMixin, mixins.ObjectPermissionMixin, BaseMixin):
    model = ConcreteObject


@pytest.fixture
def req(user_agent, user_agents):
    req = req_factory.get("/test")
    return init_request(req, user_agent, user_agents)


@pytest.fixture
def object_mixin(req):
    return ObjectMixin(request=req)


@pytest.mark.django_db(transaction=True)
class TestObjectMixin:
    def test_get_agents_return_one(self, object_mixin, user_agent):
        object_mixin.all_agents = False
        assert object_mixin.get_agents() == user_agent

    def test_get_agents_return_many(self, object_mixin, user_agents):
        object_mixin.all_agents = True
        assert object_mixin.get_agents() == user_agents

    def test_get_queryset(self, object_mixin, user_agent, accesses):
        raise NotImplementedError()

    #    object_mixin.agents = user_agent
    #    query = object_mixin.get_queryset()
    #    assert all(o.access.agent == user_agent for o in query)

    def test_dispatch(self, object_mixin):
        class Base:
            def dispatch(self, *args, **kwargs):
                pass

        class Child(mixins.ObjectMixin, Base):
            all_agents = True

        child = Child()
        child.request = object_mixin.request
        child.dispatch(child.request)
        assert child.agent == child.request.agent
        assert child.agents == child.request.agents


@pytest.fixture
def perm_mixin(req, object, access):
    object.access = access
    return ObjectPermissionMixin(request=req, object=object)


class TestObjectPermissionMixin:
    def test_get_object(self, perm_mixin):
        # we just assert that check_object_permissions is called
        call = []
        perm_mixin.check_object_permissions = lambda *a: call.append(a)
        perm_mixin.get_object()
        assert call

    def test_check_object_permissions(self, perm_mixin, req, object, access):
        perm_mixin.check_object_permissions(req, object)

    def test_check_object_permissions_from_access(self, perm_mixin, req, object, access, user_2):
        perm_mixin.request.user = user_2
        perm_mixin.check_object_permissions(req, object)

    def test_check_object_permissions_raises_permission_denied(self, perm_mixin, req, object, access, user_2):
        object.access = None
        perm_mixin.request.user = user_2
        with pytest.raises(Http404):
            perm_mixin.check_object_permissions(req, object)

    def test_get_permissions(self, perm_mixin):
        perms = perm_mixin.get_permissions()
        assert len(perms) == 1
        assert isinstance(perms[0], perm_mixin.permissions[0])


@pytest.fixture
def single_mixin(req, access):
    return SingleObjectMixin(kwargs={"uuid": access.target.uuid}, request=req, agents=access.receiver)


class TestSingleObjectMixin:
    def test_get_object(self, single_mixin, accesses, access):
        assert single_mixin.get_object() == access.target

    def test_get_object_raises_404(self, single_mixin, accesses, user_agent):
        single_mixin.kwargs["uuid"] = uuid4()
        with pytest.raises(Http404):
            single_mixin.get_object()

    def test_get_object_from_access_uuid(self, single_mixin, access):
        single_mixin.kwargs["uuid"] = access.uuid
        single_mixin.request.agents = [access.receiver]
        obj = single_mixin.get_object()
        assert (obj, access) == (access.target, access)

    def test_get_object_from_access_uuid_wrong_agent(self, single_mixin, access, group_agent):
        single_mixin.kwargs["uuid"] = access.uuid
        single_mixin.request.agents = [group_agent]
        with pytest.raises(Http404):
            single_mixin.get_object()
