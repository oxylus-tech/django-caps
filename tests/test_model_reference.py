from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.utils import timezone as tz
import pytest

from .app.models import Reference
from .conftest import assertCountEqual


@pytest.mark.django_db(transaction=True)
class TestReferenceQuerySet:
    def test_available_expiration_isnull(self, ref, user_2_agent, refs_3):
        assertCountEqual(Reference.objects.available(user_2_agent), [ref, refs_3[0]])

    def test_available_not_expired(self, ref, user_2_agent):
        ref.expiration = tz.now() + timedelta(hours=1)
        assert list(Reference.objects.available(user_2_agent)) == [ref]

    def test_available_expired(self, ref, user_2_agent):
        ref.expiration = tz.now() - timedelta(hours=1)
        ref.save(update_fields=["expiration"])
        assert not Reference.objects.available(user_2_agent).exists()

    def test_emitter(self, agents):
        for agent in agents:
            for ref in Reference.objects.emitter(agent):
                assert agent == ref.emitter, "for agent {}, ref: {}, ref.emitter: {}".format(
                    agent.ref, ref, ref.emitter.ref
                )

    def test_receiver(self, agents):
        for agent in agents:
            for ref in Reference.objects.receiver(agent):
                assert agent == ref.receiver, "for agent {}, ref: {}, ref.receiver: {}".format(
                    agent.uuid, ref, ref.receiver.uuid
                )

    def test_ref(self, refs):
        assert all(ref == Reference.objects.ref(ref.receiver, ref.uuid) for ref in refs)

    def test_ref_wrong_agent(self, refs, agents):
        for ref in refs:
            for agent in agents:
                if ref.receiver == agent:
                    continue
                with pytest.raises(Reference.DoesNotExist):
                    Reference.objects.ref(agent, ref.uuid)

    def test_refs(self, agents, refs):
        for agent in agents:
            items = {ref.uuid for ref in refs if ref.receiver == agent}
            query = Reference.objects.refs(agent, items).values_list("uuid", flat=True)
            assertCountEqual(items, list(query), "agent: " + str(agent.uuid))

    def test_refs_wrong_agent(self, agents, refs):
        for agent in agents:
            query = Reference.objects.refs(agent, set(ref.uuid for ref in refs if ref.receiver != agent))
            assert not query.exists(), "agent: " + str(agent.ref)


@pytest.mark.django_db(transaction=True)
class TestReference:
    def test_has_perm(self, ref, user_2):
        for perm in ref.grants.keys():
            assert ref.has_perm(user_2, perm)

    def test_has_perm_group_agent(self, ref, user_2):
        for perm in ref.grants.keys():
            assert ref.has_perm(user_2, perm)

    def test_has_perm_wrong_perm(self, ref, user_2, orphan_perm):
        assert not ref.has_perm(user_2, orphan_perm)

    def test_has_perm_wrong_user(self, ref, user, orphan_perm):
        for perm in ref.grants.keys():
            assert not ref.has_perm(user, perm)
        assert not ref.has_perm(user, orphan_perm)

    def test_get_all_permissions(self, ref, user_2):
        assert ref.get_all_permissions(user_2) == set(ref.grants.keys())

    def test_get_all_permissions_wrong_user(self, ref, user):
        assert not ref.get_all_permissions(user)

    def test_is_valid(self, refs):
        assert refs[2].is_valid()
        assert refs[1].is_valid()
        assert refs[0].is_valid()

    def test_share(self, ref, group_agent):
        obj = ref.share(group_agent)
        assert obj.origin == ref
        assert obj.receiver == group_agent
        assert obj.emitter == ref.receiver
        assert obj.grants.keys() == ref.grants.keys()

    def test_get_shared_grants_with_defaults(self, ref):
        result = ref.get_shared_grants()
        assert all(v == ref.grants[k] - 1 for k, v in result.items())

    def test_get_shared_grants_with_grants(self, ref):
        ref.grants = {"a": 0, "b": 1}
        grants = {
            "a": 1,  # should not exists
            "b": 1,  # upper value
            "c": 4,  # not granted
        }
        result = ref.get_shared_grants(grants)
        assert result == {"b": 0}

    def test_get_shared_kwargs(self, ref, group_agent):
        assert ref.get_shared_kwargs(group_agent, {"a": 123}) == {
            "a": 123,
            "emitter_id": ref.receiver_id,
            "receiver": group_agent,
            "origin": ref,
            "target": ref.target,
        }

    def test_get_shared_kwargs_expired_raise_permission_denied(self, ref, group_agent):
        ref.expiration = tz.now() - timedelta(hours=1)
        with pytest.raises(PermissionDenied):
            ref.get_shared_kwargs(group_agent, {})

    def test_get_shared_kwargs_expiration_fixed(self, ref, group_agent):
        ref.expiration = tz.now() + timedelta(hours=1)
        kw = ref.get_shared_kwargs(group_agent, {"expiration": tz.now() + timedelta(hours=3)})
        assert kw["expiration"] == ref.expiration

    def test_get_absolute_url(self, ref):
        assert ref.get_absolute_url()

    def test_get_absolute_url_raises_missing_target_url_name(self, ref):
        ref.target.detail_url_name = None
        with pytest.raises(ValueError, match="Missing attribute.*detail_url_name"):
            ref.get_absolute_url()
