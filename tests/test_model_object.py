# FIXME:
# TestObjectQuerySet -> inherit from TestBaseReference
import pytest

from caps.models import Reference
from caps.models.object import Object, ObjectBase

from .app.models import AbstractObject, ConcreteObject
from .conftest import assertCountEqual

__all__ = (
    "TestObjectManager",
    "TestObjectQuerySet",
)


class TestObjectManager:
    def test_get_reference_class_from_attrs(self):
        result = ObjectBase.get_reference_class("test", (Object,), attrs={"Reference": Reference})
        assert Reference is result

    def test_get_reference_class_from_attrs_fail_reference_not_subclass(self):
        with pytest.raises(ValueError):
            ObjectBase.get_reference_class(
                "test",
                (Object,),
                attrs={"Reference": object, "__module__": self.__module__},
            )

    def test_get_reference_class_from_bases(self):
        result = ObjectBase.get_reference_class(
            "test",
            (
                AbstractObject,
                ConcreteObject,
            ),
            attrs={"__module__": self.__module__},
        )
        assert AbstractObject.Reference is not result, "result should not return an abstract class"
        assert ConcreteObject.Reference is result

    def test_new_with_reference(self):
        class Meta:
            app_label = "tests.caps"

        result = ObjectBase.__new__(
            ObjectBase,
            "test",
            (ConcreteObject,),
            {"__module__": self.__module__, "Meta": Meta},
        )
        assert issubclass(result, ConcreteObject)
        assert issubclass(result.Reference, Reference)

    def test_new_generate_reference(self):
        class Meta:
            app_label = "tests.caps"

        result = ObjectBase.__new__(ObjectBase, "test", (Object,), {"__module__": self.__module__, "Meta": Meta})
        assert issubclass(result, Object)
        assert issubclass(result.Reference, Reference)


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
