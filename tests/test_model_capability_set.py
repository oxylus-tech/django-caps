import pytest
from django.core.exceptions import PermissionDenied

from caps.models import Capability, CapabilitySet
from .conftest import assertCountEqual


# Test both CapabilitySet and BaseCapabilitySet
@pytest.mark.django_db(transaction=True)
class TestCapabilitySet:
    def test_is_derived(self, caps_set_3, caps_set_2):
        assert caps_set_3.is_derived(caps_set_2)
        assert not caps_set_2.is_derived(caps_set_3)

    def test_is_derived_with_missing_in_parent(self, caps_2, caps_set_3, orphan_cap):
        subset = CapabilitySet()
        subset.capabilities = caps_2 + [orphan_cap]
        assert not caps_set_3.is_derived(subset)

    def test_derive_caps_without_arg(self, permissions, caps_set_3):
        expected = [Capability(permission=permission, max_derive=0) for permission in permissions]
        capabilities = caps_set_3.derive_caps()
        assertCountEqual(expected, capabilities)

    def test_derive_caps_with_list_arg(self, caps_set_3, caps_2):
        assert caps_set_3.derive_caps(caps_2) == caps_2

    def test_derive_caps_fail_missing_cap(self, caps_set_3, caps_2, orphan_cap):
        with pytest.raises(PermissionDenied):
            caps_set_3.derive_caps(caps_2 + [orphan_cap], raises=True)

    def test_derive_caps_fail_cap_not_derived(self, caps_set_3, caps_2):
        with pytest.raises(PermissionDenied):
            caps_2[-1].max_derive = 1000
            caps_set_3.derive_caps(caps_2, raises=True)
