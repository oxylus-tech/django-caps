import pytest
from django.core.exceptions import PermissionDenied

from caps.models import CapabilitySet
from tests.app.models import Capability
from .conftest import assertCountEqual


# Test both CapabilitySet and BaseCapabilitySet
@pytest.mark.django_db(transaction=True)
class TestCapabilitySet:
    def test_get_capabilities(self, caps_set_3):
        assert caps_set_3.get_capabilities() == caps_set_3.capabilities

    def test_is_derived(self, caps_set_3, caps_set_2):
        assert caps_set_3.is_derived(caps_set_2)
        assert not caps_set_2.is_derived(caps_set_3)

    def test_is_derived_with_missing_in_parent(self, caps_2, caps_set_3, orphan_cap):
        subset = CapabilitySet()
        subset.capabilities = caps_2 + [orphan_cap]
        assert not caps_set_3.is_derived(subset)

    def test_create_capability(self, ref_3, perm):
        cap = ref_3.create_capability(perm.id)
        assert (cap.permission_id, cap.reference) == (perm.id, ref_3)

    def test_create_capabilities(self, ref_3, permissions_id):
        caps = ref_3.create_capabilities(permissions_id)
        assert all((c.permission_id, c.reference) == (id, ref_3) for c, id in zip(caps, permissions_id))

    def test_derive_caps_without_arg(self, permissions, caps_set_3):
        expected = [Capability(permission=permission, max_derive=0) for permission in permissions]
        capabilities = caps_set_3.derive_caps()
        assertCountEqual(expected, capabilities)

    def test_derive_caps_with_list_arg(self, permissions, permissions_id, caps_set_3):
        expected = [Capability(permission=permission, max_derive=0) for permission in permissions]
        capabilities = caps_set_3.derive_caps([(id, 0) for id in permissions_id])
        assertCountEqual(expected, capabilities)

    def test_derive_caps_fail_missing_cap(self, permissions, permissions_id, caps_set_3, orphan_perm):
        with pytest.raises(PermissionDenied):
            caps_set_3.derive_caps(permissions_id + [orphan_perm.id], raises=True)

    def test_derive_caps_fail_cap_not_derived(self, permissions, permissions_id, caps_set_3):
        with pytest.raises(PermissionDenied):
            permissions_id[-1] = (permissions_id[-1], 1000)
            caps_set_3.derive_caps(permissions_id, raises=True)

    def test_get_capability_kwargs_with_tuple(self, caps_set_3):
        assert caps_set_3.get_capability_kwargs((10, 30), {"a": 12}) == (10, {"max_derive": 30, "a": 12})

    def test_get_capability_kwargs_with_permission_id(self, caps_set_3):
        assert caps_set_3.get_capability_kwargs(10, {"a": 12}) == (10, {"max_derive": None, "a": 12})

    def test_get_capability_kwargs_raise_invalid_value(self, caps_set_3):
        pass
        with pytest.raises(ValueError):
            caps_set_3.get_capability_kwargs("10", {"a": 12})
