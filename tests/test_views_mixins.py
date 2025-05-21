from uuid import uuid4

import pytest
from django.http import Http404

from caps.views import mixins
from .conftest import init_request, req_factory
from .app.models import Reference, ConcreteObject


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
    reference_class = Reference


class ObjectPermissionMixin(mixins.ObjectPermissionMixin, BaseMixin):
    reference_class = Reference


class SingleObjectMixin(mixins.SingleObjectMixin, BaseMixin):
    reference_class = Reference


class ObjectCreateMixin(mixins.ObjectCreateMixin, BaseMixin):
    reference_class = Reference


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

    def test_get_reference_queryset(self, object_mixin, user_agent, refs):
        object_mixin.agents = user_agent
        query = object_mixin.get_reference_queryset()
        assert all(r.receiver == user_agent or r.emitter == user_agent for r in query)

    def test_get_reference_class_using_class_attribute(self, object_mixin):
        object_mixin.reference_class = Reference
        assert object_mixin.get_reference_class() is Reference

    def test_get_reference_class_using_model_attribute(self, object_mixin):
        object_mixin.model = ConcreteObject
        assert object_mixin.get_reference_class() is Reference

    def test_get_reference_class_raise_missing_attribute(self, object_mixin):
        with pytest.raises(ValueError, match="There is no Reference class"):
            object_mixin.reference_class = None
            object_mixin.get_reference_class()

    def test_get_reference_class_raise_is_not_a_reference_subclass(self, object_mixin):
        object_mixin.reference_class = mixins.ObjectMixin
        with pytest.raises(ValueError, match="is not a Reference subclass"):
            object_mixin.get_reference_class()

    # def test_get_queryset(self, object_mixin, user_agent, refs):
    #    object_mixin.agents = user_agent
    #    query = object_mixin.get_queryset()
    #    assert all(o.reference.agent == user_agent for o in query)

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
def perm_mixin(req, object, ref):
    object.reference = ref
    return ObjectPermissionMixin(request=req, object=object)


class TestObjectPermissionMixin:
    def test_get_object(self, perm_mixin):
        # we just assert that check_object_permissions is called
        call = []
        perm_mixin.check_object_permissions = lambda *a: call.append(a)
        perm_mixin.get_object()
        assert call

    def test_check_object_permissions(self, perm_mixin, object, ref):
        object.reference = ref
        perm_mixin.check_object_permissions(object)

    def test_check_object_permissions_raises_permission_denied(self, perm_mixin, object, ref, user_2):
        object.reference = ref
        perm_mixin.request.user = user_2
        with pytest.raises(Http404):
            perm_mixin.check_object_permissions(object)

    def test_get_permissions(self, perm_mixin):
        perms = perm_mixin.get_permissions()
        assert len(perms) == 1
        assert isinstance(perms[0], perm_mixin.permissions[0])


@pytest.fixture
def single_mixin(req, ref, perm):
    return SingleObjectMixin(can=perm, kwargs={"uuid": ref.uuid}, request=req, agents=ref.receiver)


class TestSingleObjectMixin:
    def test_get_reference_queryset(self, single_mixin, refs, ref):
        query = single_mixin.get_reference_queryset()
        assert (query.count(), query.first()) == (1, ref)

    def test_get_object(self, single_mixin, refs, ref):
        assert single_mixin.get_object() == ref.target

    def test_get_object_raises_404(self, single_mixin, refs, user_agent):
        single_mixin.kwargs["uuid"] = uuid4()
        with pytest.raises(Http404):
            single_mixin.get_object()


@pytest.fixture
def create_mixin(req, perm):
    return ObjectCreateMixin(can=perm, request=req)


@pytest.mark.django_db(transaction=True)
class TestObjectCreateMixin:
    def test_create_reference(self, create_mixin, user_agent, object, caps_3):
        ref = create_mixin.create_reference(user_agent, object)
        assert object.reference is ref
        assert (ref.target, ref.emitter) == (object, user_agent)
