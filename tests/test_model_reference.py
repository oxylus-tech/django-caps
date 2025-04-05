import copy

import pytest

from .app.models import Reference
from .conftest import assertCountEqual


@pytest.mark.django_db(transaction=True)
class TestReferenceQuerySet:
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
            assertCountEqual(items, list(query), "agent: " + str(agent.ref))

    def test_refs_wrong_agent(self, agents, refs):
        for agent in agents:
            query = Reference.objects.refs(agent, set(ref.uuid for ref in refs if ref.receiver != agent))
            assert not query.exists(), "agent: " + str(agent.ref)


#
#    def test_action(self, refs, refs_2, caps_2):
#        action = caps_2[0].name
#        query = Reference.objects.action(caps_2[0])
#        assert all(r.can(action) for r in query)
#
#    def test_action_should_return_empty(self, refs, orphan_cap):
#        assert not Reference.objects.action(orphan_cap.name)
#
#    def test_actions(self, refs, refs_2, caps_2):
#        query = Reference.objects.actions(c.name for c in caps_2)
#        for cap in caps_2:
#            assert all(r.can(cap.name) for r in query)
#
#    def test_actions_should_return_empty(self, refs, orphan_cap):
#        assert not Reference.objects.actions([orphan_cap.name])
#
# TODO: bulk_create, bulk_update


@pytest.mark.django_db(transaction=True)
class TestReference:
    def test_is_valid(self, refs):
        assert refs[2].is_valid()
        assert refs[1].is_valid()
        assert refs[0].is_valid()

    def test_is_valid_invalid_depth(self, refs_3, refs_2):
        ref = copy.copy(refs_2[0])
        ref.depth = refs_3[0].depth

        # with exception
        with pytest.raises(ValueError):
            ref.is_valid(raises=True)
        ref.depth = 0

        # without exception
        assert not ref.is_valid()

    def test_is_derived(self, refs_3, refs_2):
        for ref in refs_3:
            derives = {r for r in refs_2 if r.target == ref.target}
            for derived in derives:
                assert ref.is_derived(derived)
                assert not derived.is_derived(ref)

    def test_is_derived_wrong_depth(self, refs):
        ref = refs[2].derive(refs[1].receiver)
        ref.depth = refs[2].depth
        assert not refs[2].is_derived(ref)

    def test_is_derived_wrong_target(self, refs, objects):
        ref = refs[2].derive(refs[1].receiver)
        ref.target = objects[1]
        assert not refs[2].is_derived(ref)

    def test_create_root(self, user_agent, object, caps_3):
        ref = Reference.create_root(user_agent, object)
        assert ref.receiver == ref.emitter == user_agent
        assert ref.origin is None
        assertCountEqual(
            ref.capabilities.all().values("permission_id", "max_derive"),
            [{"permission_id": c.permission_id, "max_derive": c.max_derive} for c in caps_3],
        )

    def test_create_root_raise_with_origin(self, user_agent, object, refs):
        with pytest.raises(ValueError):
            Reference.create_root(user_agent, object, origin=refs[0])

    def test_create_root_raise_with_reference_already_present(self, user_agent, object, ref):
        with pytest.raises(ValueError):
            Reference.create_root(user_agent, object)

    def test_derive(self, ref, group_agent):
        obj = ref.derive(group_agent)
        assert obj.origin == ref
        assert obj.depth == ref.depth + 1
        assert obj.receiver == group_agent
        assert obj.emitter == ref.receiver
        assertCountEqual(
            obj.capabilities.all().values_list("permission_id", flat=True),
            ref.capabilities.all().values_list("permission_id", flat=True),
        )

    def test__get_derived_kwargs(self, ref, group_agent):
        assert ref._get_derived_kwargs(group_agent, {"a": 123}) == {
            "a": 123,
            "receiver": group_agent,
            "depth": ref.depth + 1,
            "origin": ref,
            "target": ref.target,
        }
