import pytest

from rest_framework import status

from caps.views import api
from .app.models import Reference, ConcreteObject
from .app.serializers import ConcreteObjectSerializer
from .conftest import req_factory, init_request
from .test_views_mixins import BaseMixin


class ObjectViewSetMixin(api.ObjectViewSet, BaseMixin):
    queryset = ConcreteObject.objects.all()
    serializer_class = ConcreteObjectSerializer


@pytest.fixture
def req(user_agent, user_agents):
    req = req_factory.get("/test")
    return init_request(req, user_agent, user_agents)


@pytest.fixture
def viewset_mixin(req, user_agent):
    return ObjectViewSetMixin(request=req, agent=user_agent)


@pytest.fixture
def ref_viewset(req):
    req.query_params = req.GET
    return api.ReferenceViewSet(request=req, model=Reference, queryset=Reference.objects.all(), action="list")


@pytest.mark.django_db(transaction=True)
class TestObjectViewSet:
    def test_perform_create(self, viewset_mixin, req, user_agent):
        ser = ConcreteObjectSerializer(data={"name": "Name"}, context={"request": req})
        ser.is_valid()
        viewset_mixin.perform_create(ser)

        assert isinstance(ser.instance.reference, Reference)
        assert ser.instance.reference.receiver == user_agent

    def test_get_reference_queryset_for_detail(self, viewset_mixin, ref):
        viewset_mixin.detail = True
        viewset_mixin.kwargs = {"uuid": ref.uuid}
        query = viewset_mixin.get_reference_queryset()
        assert list(query) == [ref]


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
