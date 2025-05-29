import pytest

from rest_framework import status

from caps.views import api
from .app.models import Access, ConcreteObject
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
def access_viewset(req):
    req.query_params = req.GET
    return api.AccessViewSet(request=req, model=Access, queryset=Access.objects.all(), action="list")


@pytest.mark.django_db(transaction=True)
class TestObjectViewSet:
    def test_perform_create(self, viewset_mixin, req, user_agent):
        ser = ConcreteObjectSerializer(data={"name": "Name"}, context={"request": req})
        ser.is_valid()
        viewset_mixin.perform_create(ser)

        assert ser.instance.owner == user_agent

    def test_get_queryset(self):
        raise NotImplementedError()

    def test_share(self):
        raise NotImplementedError()


class TestAccessViewSet:
    def test_get_queryset(self, access_viewset, user_agents, accesses_3, accesses_2):
        access_viewset.action = "list"
        query = access_viewset.get_queryset()

        assert all(q.emitter in user_agents or q.receiver in user_agents for q in query)
        assert any(q.emitter in user_agents for q in query)
        assert any(q.receiver in user_agents for q in query)

    def test_get_queryset_for_share(self, access_viewset, user_agents, accesses_3, accesses_2):
        access_viewset.action = "share"
        query = access_viewset.get_queryset()
        assert all(q.receiver in user_agents for q in query)

    def test_share(self, access_viewset, user_agent, group_agent, access):
        access_viewset.kwargs = {"uuid": access.uuid}
        access_viewset.request.data = {
            "receiver": group_agent.uuid,
            "grants": access.grants,
        }
        resp = access_viewset.share(access_viewset.request)
        assert resp.data["origin"] == str(access.uuid)

    def test_share_invalid(self, access_viewset, access, group_agent):
        access_viewset.kwargs = {"uuid": access.uuid}
        access_viewset.request.data = {"receiver": group_agent.uuid, "grants": "list"}
        resp = access_viewset.share(access_viewset.request)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
