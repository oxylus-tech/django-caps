import pytest

from rest_framework import status

from caps.views import api
from .app.models import Reference
from .conftest import req_factory, init_request
from .test_views_mixins import BaseMixin


class ObjectViewSetMixin(api.ObjectViewSet, BaseMixin):
    reference_class = Reference


@pytest.fixture
def req(user_agent, user_agents):
    req = req_factory.get("/test")
    return init_request(req, user_agent, user_agents)


@pytest.fixture
def viewset_mixin(req):
    return ObjectViewSetMixin(request=req)


@pytest.fixture
def ref_viewset(req):
    req.query_params = req.GET
    return api.ReferenceViewSet(request=req, model=Reference, queryset=Reference.objects.all(), action="list")


@pytest.mark.django_db(transaction=True)
class TestObjectViewSet:
    def test_perform_create(self, viewset_mixin):
        raise NotImplementedError()

    def test_get_reference_queryset_for_detail(self, viewset_mixin):
        raise NotImplementedError()


class TestReferenceViewSet:
    def test_get_queryset(self, ref_viewset, user_agents, refs_3, refs_2):
        ref_viewset.action = "list"
        query = ref_viewset.get_queryset()

        assert all(q.emitter in user_agents or q.receiver in user_agents for q in query)
        assert any(q.emitter in user_agents for q in query)
        assert any(q.receiver in user_agents for q in query)

    def test_get_queryset_for_derive(self, ref_viewset, user_agents, refs_3, refs_2):
        ref_viewset.action = "derive"
        query = ref_viewset.get_queryset()
        assert all(q.receiver in user_agents for q in query)

    def test_derive(self, ref_viewset, user_agent, group_agent, ref):
        ref_viewset.kwargs = {"uuid": ref.uuid}
        ref_viewset.request.data = {
            "receiver": group_agent.uuid,
            "capabilities": [c.serialize() for c in ref.capabilities],
        }
        resp = ref_viewset.derive(ref_viewset.request)
        assert resp.data["origin"] == ref.uuid

    def test_derive_invalid(self, ref_viewset, ref, group_agent):
        ref_viewset.kwargs = {"uuid": ref.uuid}
        ref_viewset.request.data = {"receiver": group_agent.uuid, "caps": "list"}
        resp = ref_viewset.derive(ref_viewset.request)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
