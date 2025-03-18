import pytest
from django.core.exceptions import PermissionDenied

from caps.models import Capability, CapabilitySet
from .conftest import assertCountEqual


# Test both CapabilitySet and BaseCapabilitySet
@pytest.mark.django_db(transaction=True)
class TestCapabilitySet:
    # TODO: derive_caps, aderive_caps, aderive
    def test_is_derived(self, caps_set_3, caps_set_2):
        assert caps_set_3.is_derived(caps_set_2)
        assert not caps_set_2.is_derived(caps_set_3)

    def test_is_derived_with_missing_in_parent(self, caps_2, caps_set_3):
        subset = CapabilitySet(caps_2)
        cap = Capability(name="missing_one", max_derive=10)
        subset.capabilities.append(cap)
        assert not caps_set_3.is_derived(subset)

    def test_derive_caps_without_arg(self, caps_names, caps_set_3):
        expected = [Capability(name=name, max_derive=0) for name in caps_names]
        capabilities = caps_set_3.derive_caps()
        assertCountEqual(expected, capabilities)

    def test_derive_caps_with_string_list_arg(self, caps_names, caps_set_3):
        expected = [Capability(name=name, max_derive=0) for name in caps_names]
        capabilities = caps_set_3.derive_caps(caps_names)
        assertCountEqual(expected, capabilities)

    def test_derive_caps_with_tuple_list_arg(self, caps_names, caps_set_3):
        args = [(name, i % 2) for i, name in enumerate(caps_names)]
        expected = [Capability(name=name, max_derive=i) for name, i in args]
        capabilities = caps_set_3.derive_caps(args)
        assertCountEqual(expected, capabilities)

    def test_derive_caps_fail_missing_cap(self, caps_names, caps_set_3):
        with pytest.raises(PermissionDenied):
            caps_set_3.derive_caps(caps_names + ["missing_one"])

    def test_derive_caps_fail_cap_not_derived(self, caps_names, caps_set_2):
        with pytest.raises(PermissionDenied):
            caps = caps_names[:-1] + [(caps_names[-1], 10)]
            caps_set_2.derive_caps(caps)

    def test_derive_caps_fail_cant_derive(self, caps_names, caps_set_2):
        caps = caps_set_2.derive_caps(caps_names)
        set = CapabilitySet(caps)
        with pytest.raises(PermissionDenied):
            set.derive_caps(caps_names)


#    def test_add(self):
#        capability = Capability(name="action", max_derive=1)
#        self.caps_set_2.add(capability)
#        self.assertEqual("action", self.caps_set_2["action"].name)
#        with self.assertRaises(KeyError):
#            self.caps_set_2.add(capability)
#
#    def test_extend(self):
#        self.caps_set_2.extend([Capability(name="action", max_derive=1)])
#        self.assertEqual("action", self.caps_set_2["action"].name)
