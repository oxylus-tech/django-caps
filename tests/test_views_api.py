import pytest

from caps.views import api
from .app.models import Reference
from .conftest import req_factory, init_request
from .test_views_mixins import BaseMixin


class ObjectViewSetMixin(api.ObjectViewSetMixin, BaseMixin):
    reference_class = Reference


@pytest.fixture
def req(user_agent, user_agents):
    req = req_factory.get("/test")
    return init_request(req, user_agent, user_agents)


@pytest.fixture
def viewset_mixin(req):
    return ObjectViewSetMixin(request=req)


@pytest.mark.django_db(transaction=True)
class TestObjectViewSetMixin:
    def test_get_can_all_q(self, viewset_mixin):
        viewset_mixin.action = "list"
        assert viewset_mixin.get_can_all_q() == viewset_mixin._get_can_all_q(Reference, api.ObjectListAPIView.can)

    def test_get_can_all_q_without_can_for_action(self, viewset_mixin):
        viewset_mixin.action = "publish"
        assert viewset_mixin.get_can_all_q() == []
