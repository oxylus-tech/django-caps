import pytest

from django.core.exceptions import PermissionDenied
from rest_framework import status

from caps.views import api
from .app.models import Access, ConcreteOwned
from .app.serializers import ConcreteOwnedSerializer
from .conftest import api_req_factory, init_api_request
from .test_views_mixins import BaseMixin


class OwnedViewSetMixin(api.OwnedViewSet, BaseMixin):
    queryset = ConcreteOwned.objects.all()
    serializer_class = ConcreteOwnedSerializer


@pytest.fixture
def req(user, user_agent, user_agents):
    return init_api_request(api_req_factory.get("/test"), user)


@pytest.fixture
def post_req(user, user_agents):
    return init_api_request(api_req_factory.post("/test", {}), user)


@pytest.fixture
def viewset_mixin(req, user_agent, object):
    return OwnedViewSetMixin(request=req, agent=user_agent, kwargs={"uuid": str(object.uuid)})


@pytest.fixture
def access_viewset(req):
    req.query_params = req.GET
    return api.AccessViewSet(request=req, model=Access, queryset=Access.objects.all(), action="list")


@pytest.mark.django_db(transaction=True)
class TestOwnedViewSet:
    def test_perform_create(self, viewset_mixin, req, user_agent, user_agents):
        ser = ConcreteOwnedSerializer(
            data={"name": "Name"}, context={"request": req, "agent": user_agent, "agents": user_agents}
        )
        ser.is_valid(raise_exception=True)
        viewset_mixin.perform_create(ser)

        assert ser.instance.owner == user_agent

    def test_perform_create_with_owner(self, viewset_mixin, req, user_agent, user_agents):
        ser = ConcreteOwnedSerializer(
            data={"name": "Name", "owner": str(user_agent.uuid)},
            context={"request": req, "agent": user_agent, "agents": user_agents},
        )
        ser.is_valid(raise_exception=True)
        viewset_mixin.perform_create(ser)

        assert ser.instance.owner == user_agent

    def test_get_access_queryset_with_action_share(self, viewset_mixin):
        viewset_mixin.action = "share"
        assert viewset_mixin.get_access_queryset() is None

    def test_share_valid(self, viewset_mixin, post_req, user_2_agent):
        viewset_mixin.action = "share"
        viewset_mixin.request = post_req
        post_req.data = {"receiver": user_2_agent.uuid, "grants": {"caps_test.view_concreteowned": 1}}
        resp = viewset_mixin.share(post_req)
        assert resp.status_code == 201

    def test_share_invalid_data(self, viewset_mixin, post_req):
        viewset_mixin.action = "share"
        viewset_mixin.request = post_req
        post_req.data = {"grants": {"caps_test.view_concreteowned": 1}}
        resp = viewset_mixin.share(post_req)
        assert resp.status_code == 400

    def test_share_invalid_grants(self, viewset_mixin, post_req, user_2_agent):
        viewset_mixin.action = "share"
        viewset_mixin.request = post_req
        post_req.data = {"receiver": user_2_agent.uuid, "grants": {"auth.view_user": 1}}
        with pytest.raises(PermissionDenied):
            viewset_mixin.share(post_req)


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


@pytest.fixture
def agent_viewset(req):
    return api.AgentViewSet(request=req)


class TestAgentViewSet:
    def test_user_with_provided_id_is_request_user(self, agent_viewset, user, user_agents):
        agent_viewset.request.GET = {"user": user.id}
        resp = agent_viewset.user()
        assert resp.status_code == 200

        for vals in resp.data:
            assert vals["user"] == user.id or any(g.id == vals["group"] for g in user.groups.all())

    def test_user_with_provided_id_raises_permission_denied(self, agent_viewset, user_2):
        agent_viewset.request.GET = {"user": user_2.id}
        with pytest.raises(PermissionDenied):
            agent_viewset.user()

    def test_user_with_provided_id_has_perm(self, agent_viewset, user_admin, user):
        agent_viewset.request.user = user_admin
        agent_viewset.request.GET = {"user": user.id}
        resp = agent_viewset.user()
        assert resp.status_code == 200

    def test_user_without_id(self, agent_viewset, user):
        resp = agent_viewset.user()
        assert resp.status_code == 200

        for vals in resp.data:
            assert vals["user"] == user.id or any(g.id == vals["group"] for g in user.groups.all())
