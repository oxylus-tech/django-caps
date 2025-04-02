# FIXME:
# TestObjectQuerySet -> inherit from TestBaseReference
import pytest


from .app.models import ConcreteObject
from .conftest import assertCountEqual


class TestObjectQuerySet:
    def test_ref(self, refs):
        for ref in refs:
            result = ConcreteObject.objects.ref(ref.receiver, ref.uuid)
            assert result is not None
            assert ref == result.reference

    def test_ref_wrong_agent(self, refs, agents):
        for ref in refs:
            agents = (r for r in agents if r != ref.receiver)
            for agent in agents:
                with pytest.raises(ConcreteObject.DoesNotExist):
                    ConcreteObject.objects.ref(agent, ref.uuid)

    def test_refs(self, agents, refs):
        for agent in agents:
            items = [r.uuid for r in refs if r.receiver == agent]
            result = ConcreteObject.objects.refs(agent, items)
            assertCountEqual(items, (r.reference.uuid for r in result))

    def test_refs_wrong_refs(self, agents, refs):
        for agent in agents:
            result = ConcreteObject.objects.refs(agent, (r.uuid for r in refs if r.receiver != agent))
            assert not result.exists()
