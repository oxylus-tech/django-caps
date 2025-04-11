import pytest

from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType

from .conftest import assertCountEqual
from tests.app.models import Capability, Reference, ConcreteObject


@pytest.mark.django_db(transaction=True)
class TestCapabilityQuerySet:
    def test_can_one_lookup_with_permission(self, permissions):
        perm = permissions[0]
        assert Capability.objects.can_one_lookup(perm) == {"permission__id": perm.id}

    def test_can_one_lookup_with_permission_id(self):
        assert Capability.objects.can_one_lookup(12) == {"permission__id": 12}

    def test_can_one_lookup_with_permission_codename(self):
        ct = ContentType.objects.get_for_model(ConcreteObject)
        assert Capability.objects.can_one_lookup("view", model=ConcreteObject) == {
            "permission__codename": "view_concreteobject",
            "permission__content_type": ct,
        }

    def test_can_one_lookup_with_permission_codename_missing_model(self):
        with pytest.raises(ValueError):
            Capability.objects.can_one_lookup("view")

    def test_can_one_lookup_raises_invalid_permission_type(self):
        with pytest.raises(ValueError):
            Capability.objects.can_one_lookup(b"12")

    def test_can_one_lookup_with_content_type(self):
        ct = ContentType.objects.all().first()
        assert Capability.objects.can_one_lookup(("test", ct)) == {
            "permission__content_type": ct,
            "permission__codename": f"test_{ct.model}",
        }

    def test_can_one_lookup_with_content_type_model(self):
        ct = ContentType.objects.all().first()
        model = ct.model_class()
        assert Capability.objects.can_one_lookup(("test", model)) == {
            "permission__content_type": ct,
            "permission__codename": f"test_{ct.model}",
        }

    def test_can_one_lookup_raises_invalid_content_type(self):
        with pytest.raises(ValueError):
            Capability.objects.can_one_lookup(("test", "invalid"))

    def test_can_with_one_permission(self, caps_3, permissions):
        caps = list(Capability.objects.can(permissions[0]))
        assert caps == [caps_3[0]]

    def test_can_with_many_permissions(self, permissions, caps_3):
        caps = Capability.objects.can(permissions[0:1])
        assertCountEqual(caps, caps_3[0:1])

    # TODO: can_q, can_all_q

    def test_initials(self, caps_3, user_agents):
        cap, *caps = caps_3

        obj = ConcreteObject.objects.create(name="test")
        cap.reference = Reference.objects.create(target=obj, receiver=user_agents[0])
        cap.save()

        query = Capability.objects.initials()
        assertCountEqual(query, caps)


@pytest.mark.django_db(transaction=True)
class TestCapability:
    def test_get_reference_class(self):
        assert Capability.get_reference_class() is Reference

    def test_get_object_class(self):
        assert Capability.get_object_class() is ConcreteObject

    def test_can_derive(self):
        assert not Capability(max_derive=0).can_derive()
        assert Capability(max_derive=1).can_derive()
        assert Capability(max_derive=2).can_derive()

    def test_derive(self, perm):
        parent = Capability(permission=perm, max_derive=1)
        child = parent.derive()
        assert parent.permission == child.permission
        assert parent.max_derive - 1 == child.max_derive

    def test_derive_fail(self, perm):
        parent = Capability(permission=perm, max_derive=0)
        with pytest.raises(PermissionDenied):
            parent.derive()

    def test_is_derived(self, perm):
        parent = Capability(permission=perm, max_derive=3)
        child = parent.derive()
        assert parent.is_derived(child)
        # test reverse relation direction
        assert not child.is_derived(parent)

    def test_is_derived_false_max_derive(self, perm):
        parent = Capability(permission=perm, max_derive=1)
        child = Capability(permission=perm, max_derive=2)
        assert not parent.is_derived(child)

    def test_is_derived_false_different_perm(self, permissions):
        parent = Capability(permission=permissions[0], max_derive=1)
        child = Capability(permission=permissions[1], max_derive=2)
        assert not parent.is_derived(child) and not child.is_derived(parent)

    def test_is_derived_leaf_false(self, perm):
        parent = Capability(permission=perm, max_derive=0)
        child = Capability(permission=perm, max_derive=-1)
        assert not parent.is_derived(child)

    def test_is_derived_nested(self, perm):
        parent = Capability(permission=perm, max_derive=4)
        child = parent.derive().derive().derive()
        assert parent.is_derived(child)
