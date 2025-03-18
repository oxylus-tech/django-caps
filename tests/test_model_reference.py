import copy

import pytest
from django.core.exceptions import PermissionDenied

from .app.models import ConcreteReference
from .conftest import assertCountEqual


@pytest.mark.django_db(transaction=True)
class TestReference:
    def test_is_valid(self, refs):
        assert refs[2].is_valid()
        assert refs[1].is_valid()
        assert refs[0].is_valid()

    def test_is_valid_invalid_depth(self, refs_3, refs_1):
        ref = copy.copy(refs_1[0])
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

    # caps: caps_3 (used by refs_3
    def test_create(self, refs, agents, caps_3):
        capabilities = list(refs[0].get_capabilities())
        assert agents[0] == refs[0].emitter
        assert agents[0] == refs[0].receiver
        assert 0 == refs[0].depth
        assertCountEqual(caps_3, capabilities)

    def test_create_fail_origin(self, agents, objects, caps_1, refs):
        with pytest.raises(ValueError):
            ConcreteReference.create(agents[0], objects[1], caps_1, origin=refs[0])

    def test_derive(self):
        raise NotImplementedError("test not done")

    def test_can(self, refs_1, caps_1):
        ref = refs_1[0]
        assert all(ref.can(c.name) for c in caps_1)

    def test_can_raises_permission_denied(self, refs_1, orphan_cap):
        ref = refs_1[0]
        with pytest.raises(PermissionDenied):
            ref.can(orphan_cap.name, raises=True)


@pytest.mark.django_db(transaction=True)
class TestReferenceQuerySet:
    def test_emitter(self, agents):
        for agent in agents:
            for ref in ConcreteReference.objects.emitter(agent):
                assert agent == ref.emitter, "for agent {}, ref: {}, ref.emitter: {}".format(
                    agent.ref, ref, ref.emitter.ref
                )

    def test_receiver(self, agents):
        for agent in agents:
            for ref in ConcreteReference.objects.receiver(agent):
                assert agent == ref.receiver, "for agent {}, ref: {}, ref.receiver: {}".format(
                    agent.uuid, ref, ref.receiver.uuid
                )

    def test_ref(self, refs):
        assert all(ref == ConcreteReference.objects.ref(ref.receiver, ref.uuid) for ref in refs)

    def test_ref_wrong_agent(self, refs, agents):
        for ref in refs:
            for agent in agents:
                if ref.receiver == agent:
                    continue
                with pytest.raises(ConcreteReference.DoesNotExist):
                    ConcreteReference.objects.ref(agent, ref.uuid)

    def test_refs(self, agents, refs):
        for agent in agents:
            items = {ref.uuid for ref in refs if ref.receiver == agent}
            query = ConcreteReference.objects.refs(agent, items).values_list("uuid", flat=True)
            assertCountEqual(items, list(query), "agent: " + str(agent.ref))

    def test_refs_wrong_agent(self, agents, refs):
        for agent in agents:
            query = ConcreteReference.objects.refs(agent, set(ref.uuid for ref in refs if ref.receiver != agent))
            assert not query.exists(), "agent: " + str(agent.ref)

    def test_action(self, refs, refs_2, caps_2):
        action = caps_2[0].name
        query = ConcreteReference.objects.action(caps_2[0])
        assert all(r.can(action) for r in query)

    def test_action_should_return_empty(self, refs, orphan_cap):
        assert not ConcreteReference.objects.action(orphan_cap.name)
        
    def test_actions(self, refs, refs_2, caps_2):
        query = ConcreteReference.objects.actions(c.name for c in caps_2)
        for cap in caps_2:
            assert all(r.can(cap.name) for r in query)

    def test_actions_should_return_empty(self, refs, orphan_cap):
        assert not ConcreteReference.objects.actions([orphan_cap.name])
        
    # TODO: bulk_create, bulk_update
