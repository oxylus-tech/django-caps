import pytest

from django.core.exceptions import PermissionDenied

from caps.models import Capability


@pytest.mark.django_db(transaction=True)
class TestCapability:
    def test_can_derive(self, perm):
        assert not Capability(perm, 0).can_derive()
        assert Capability(perm, 1).can_derive()
        assert Capability(perm, 2).can_derive()

    def test_derive(self, perm):
        parent = Capability(perm, 1)
        child = parent.derive()
        assert parent.permission == child.permission
        assert parent.max_derive - 1 == child.max_derive

    def test_derive_fail(self, perm):
        parent = Capability(perm, 0)
        with pytest.raises(PermissionDenied):
            parent.derive()

    def test_is_derived(self, perm):
        parent = Capability(perm, 3)
        child = parent.derive()
        assert parent.is_derived(child)
        # test reverse relation direction
        assert not child.is_derived(parent)

    def test_is_derived_false_max_derive(self, perm):
        parent, child = Capability(perm, 1), Capability(perm, 2)
        assert not parent.is_derived(child)

    def test_is_derived_false_different_perm(self, permissions):
        parent, child = Capability(permissions[0], 1), Capability(permissions[1], 2)
        assert not parent.is_derived(child) and not child.is_derived(parent)

    def test_is_derived_leaf_false(self, perm):
        parent, child = Capability(perm, 0), Capability(perm, -1)
        assert not parent.is_derived(child)

    def test_is_derived_nested(self, perm):
        parent = Capability(permission=perm, max_derive=4)
        child = parent.derive().derive().derive()
        assert parent.is_derived(child)

    # TODO: __eq__, __contains__
