from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.utils import timezone as tz
import pytest

from .app.models import Access
from .conftest import assertCountEqual


@pytest.mark.django_db(transaction=True)
class TestAccessQuerySet:
    def test_available_expiration_isnull(self, access, user_2_agent, accesses_3):
        assertCountEqual(Access.objects.available(user_2_agent), [access, accesses_3[0]])

    def test_available_not_expired(self, access, user_2_agent):
        access.expiration = tz.now() + timedelta(hours=1)
        assert list(Access.objects.available(user_2_agent)) == [access]

    def test_available_expired(self, access, user_2_agent):
        access.expiration = tz.now() - timedelta(hours=1)
        access.save(update_fields=["expiration"])
        assert not Access.objects.available(user_2_agent).exists()

    def test_emitter(self, agents):
        for agent in agents:
            for access in Access.objects.emitter(agent):
                assert agent == access.emitter, "for agent {}, access: {}, access.emitter: {}".format(
                    agent.access, access, access.emitter.access
                )

    def test_receiver(self, agents):
        for agent in agents:
            for access in Access.objects.receiver(agent):
                assert agent == access.receiver, "for agent {}, access: {}, access.receiver: {}".format(
                    agent.uuid, access, access.receiver.uuid
                )

    def test_access(self, accesses):
        assert all(access == Access.objects.access(access.receiver, access.uuid) for access in accesses)

    def test_access_wrong_agent(self, accesses, agents):
        for access in accesses:
            for agent in agents:
                if access.receiver == agent:
                    continue
                with pytest.raises(Access.DoesNotExist):
                    Access.objects.access(agent, access.uuid)

    def test_accesses(self, agents, accesses):
        for agent in agents:
            items = {access.uuid for access in accesses if access.receiver == agent}
            query = Access.objects.accesses(agent, items).values_list("uuid", flat=True)
            assertCountEqual(items, list(query), "agent: " + str(agent.uuid))

    def test_accesses_wrong_agent(self, agents, accesses):
        for agent in agents:
            query = Access.objects.accesses(agent, set(access.uuid for access in accesses if access.receiver != agent))
            assert not query.exists(), "agent: " + str(agent.access)


@pytest.mark.django_db(transaction=True)
class TestAccess:
    def test_has_perm(self, access, user_2):
        for perm in access.grants.keys():
            assert access.has_perm(user_2, perm)

    def test_has_perm_group_agent(self, access, user_2):
        for perm in access.grants.keys():
            assert access.has_perm(user_2, perm)

    def test_has_perm_wrong_perm(self, access, user_2, orphan_perm):
        assert not access.has_perm(user_2, orphan_perm)

    def test_has_perm_wrong_user(self, access, user, orphan_perm):
        for perm in access.grants.keys():
            assert not access.has_perm(user, perm)
        assert not access.has_perm(user, orphan_perm)

    def test_get_all_permissions(self, access, user_2):
        assert access.get_all_permissions(user_2) == set(access.grants.keys())

    def test_get_all_permissions_wrong_user(self, access, user):
        assert not access.get_all_permissions(user)

    def test_is_valid(self, accesses):
        assert accesses[2].is_valid()
        assert accesses[1].is_valid()
        assert accesses[0].is_valid()

    def test_share(self, access, group_agent):
        obj = access.share(group_agent)
        assert obj.origin == access
        assert obj.receiver == group_agent
        assert obj.emitter == access.receiver
        assert obj.grants.keys() == access.grants.keys()

    def test_get_share_grants_with_defaults(self, access):
        result = access.get_share_grants()
        assert all(v == access.grants[k] - 1 for k, v in result.items())

    def test_get_share_grants_with_grants(self, access):
        access.grants = {"a": 0, "b": 1}
        grants = {
            "a": 1,  # should not exists
            "b": 1,  # upper value
            "c": 4,  # not granted
        }
        result = access.get_share_grants(grants)
        assert result == {"b": 0}

    def test_get_share_kwargs(self, access, group_agent):
        assert access.get_share_kwargs(group_agent, {"a": 123}) == {
            "a": 123,
            "emitter_id": access.receiver_id,
            "receiver": group_agent,
            "origin": access,
            "target": access.target,
        }

    def test_get_share_kwargs_expired_raise_permission_denied(self, access, group_agent):
        access.expiration = tz.now() - timedelta(hours=1)
        with pytest.raises(PermissionDenied):
            access.get_share_kwargs(group_agent, {})

    def test_get_share_kwargs_expiration_fixed(self, access, group_agent):
        access.expiration = tz.now() + timedelta(hours=1)
        kw = access.get_share_kwargs(group_agent, {"expiration": tz.now() + timedelta(hours=3)})
        assert kw["expiration"] == access.expiration

    def test_get_absolute_url(self, access):
        assert access.get_absolute_url()

    def test_get_absolute_url_raises_missing_target_url_name(self, access):
        access.target.detail_url_name = None
        with pytest.raises(ValueError, match="Missing attribute.*detail_url_name"):
            access.get_absolute_url()
