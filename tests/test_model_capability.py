import pytest
from asgiref.sync import sync_to_async
from django.core.exceptions import PermissionDenied

__all__ = (
    "TestCapabilityQuerySet",
    "TestCapability",
)


from caps.models import Capability


@pytest.mark.django_db(transaction=True)
class TestCapabilityQuerySet:
    def test_get_or_create_many(self):
        subset = [
            Capability(name="action_1", max_derive=1),
            Capability(name="action_2", max_derive=1),
        ]
        subset[0].save()
        result = Capability.objects.get_or_create_many(subset)

        assert len(subset) == result.count()
        assert all(item.pk is not None for item in subset)
        assert all(item in subset for item in result)

    @pytest.mark.asyncio
    async def test_aget_or_create_many(self):
        subset = [
            Capability(name="action_1", max_derive=1),
            Capability(name="action_2", max_derive=1),
        ]
        sync_to_async(subset[0].save)
        result = await Capability.objects.aget_or_create_many(subset)

        assert len(subset) == await result.acount()
        for item in subset:
            assert item.pk is not None

    # TODO: test__get_items_queryset


@pytest.mark.django_db(transaction=True)
class TestCapability:
    def test_into_tuple(self):
        expected = Capability(name="action", max_derive=12)
        values = (
            (expected.name, expected.max_derive),
            [expected.name, expected.max_derive],
            Capability(name=expected.name, max_derive=expected.max_derive),
        )
        for value in values:
            capability = Capability.into(value)
            assert expected == capability

        # TODO string -> max_derive=0

    def test_into_raises(self):
        with pytest.raises(NotImplementedError):
            Capability.into(12.1)

    def test_can_derive(self):
        assert not Capability(max_derive=0).can_derive()
        assert Capability(max_derive=1).can_derive()
        assert Capability(max_derive=2).can_derive()

    def test_derive(self):
        parent = Capability(name="test", max_derive=1)
        child = parent.derive()
        assert parent.name == child.name
        assert parent.max_derive - 1 == child.max_derive

    def test_derive_fail(self):
        parent = Capability(name="test", max_derive=0)
        with pytest.raises(PermissionDenied):
            parent.derive()

    def test_is_derived(self):
        parent = Capability(name="test", max_derive=3)
        child = parent.derive()
        assert parent.is_derived(child)
        # test reverse relation direction
        assert not child.is_derived(parent)

    def test_is_derived_false_max_derive(self):
        parent = Capability(name="test", max_derive=1)
        child = Capability(name="test", max_derive=2)
        assert not parent.is_derived(child)

    def test_is_derived_leaf_false(self):
        parent = Capability(name="test", max_derive=0)
        child = Capability(name="test", max_derive=-1)
        assert not parent.is_derived(child)

    def test_is_derived_nested(self):
        parent = Capability(name="test", max_derive=4)
        child = parent.derive().derive().derive()
        assert parent.is_derived(child)
