# FIXME:
# TestObjectQuerySet -> inherit from TestBaseReference


from .app.models import ConcreteObject, Reference
from .conftest import assertCountEqual


class TestObjectQuerySet:
    def test_refs(self, agents, refs):
        for agent in agents:
            query = Reference.objects.receiver(agent)
            q_uuids = list(query.values_list("uuid", flat=True))
            result = ConcreteObject.objects.refs(query)
            uuids = [r.reference.uuid for r in result]
            assertCountEqual(uuids, q_uuids)
