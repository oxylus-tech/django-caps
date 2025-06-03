from uuid import uuid4

import pytest
from django.http import Http404

from caps.views import mixins
from .conftest import init_request, req_factory
from .app.models import ConcreteOwned


class BaseMixin:
    object = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def dispatch(self, request, *args, **kwargs):
        pass

    def get_queryset(self):
        return ConcreteOwned.objects.all()

    def get_object(self):
        return self.object


class OwnedMixin(mixins.OwnedMixin, BaseMixin):
    model = ConcreteOwned


class OwnedPermissionMixin(mixins.OwnedPermissionMixin, BaseMixin):
    model = ConcreteOwned


class SingleOwnedMixin(mixins.SingleOwnedMixin, mixins.OwnedPermissionMixin, BaseMixin):
    model = ConcreteOwned


@pytest.fixture
def req(user, user_agents):
    return init_request(req_factory.get("/test"), user)


@pytest.fixture
def object_mixin(req):
    return OwnedMixin(request=req)


@pytest.mark.django_db(transaction=True)
class TestOwnedMixin:
    pass


@pytest.fixture
def perm_mixin(req, object, access):
    object.access = access
    return OwnedPermissionMixin(request=req, object=object)


class TestOwnedPermissionMixin:
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
def single_mixin(req, access, user_2):
    req.user = user_2
    return SingleOwnedMixin(kwargs={"uuid": access.target.uuid}, request=req)


class TestSingleOwnedMixin:
    def test_get_object(self, single_mixin, accesses, access, user):
        single_mixin.request.user = user
        assert single_mixin.get_object() == access.target

    def test_get_object_raises_404(self, single_mixin, accesses, user_agent):
        single_mixin.kwargs["uuid"] = uuid4()
        with pytest.raises(Http404):
            single_mixin.get_object()

    def test_get_object_from_access_uuid(self, single_mixin, access, user_2):
        single_mixin.kwargs["uuid"] = access.uuid
        single_mixin.request.user = user_2
        obj = single_mixin.get_object()
        assert (obj, access) == (access.target, access)

    def test_get_object_from_access_uuid_wrong_agent(self, single_mixin, access, user_3):
        single_mixin.kwargs["uuid"] = access.uuid
        single_mixin.request.user = user_3
        with pytest.raises(Http404):
            single_mixin.get_object()
