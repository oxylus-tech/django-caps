import pytest

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


class TestObject:
    def test_get_absolute_url(self, object, ref):
        setattr(object, "reference", ref)
        assert object.get_absolute_url() == ref.get_absolute_url()

    def test_get_absolute_url_raises_missing_reference(self, object):
        setattr(object, "reference", None)
        with pytest.raises(ValueError, match="ObjectQuerySet.refs"):
            object.get_absolute_url()
