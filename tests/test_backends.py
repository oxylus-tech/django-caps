import pytest

from caps import backends


@pytest.fixture
def perm_backend():
    return backends.PermissionsBackend()


class TestCapsBackend:
    def test_has_perm(self, perm_backend, user, object, ref, perm, orphan_perm):
        assert not perm_backend.has_perm(user, perm, object)
        assert not perm_backend.has_perm(user, perm)

        # set reference on object for the following tests
        object.reference = ref
        assert perm_backend.has_perm(user, perm, object)
        assert perm_backend.has_perm(user, perm, ref)
        assert not perm_backend.has_perm(user, orphan_perm, object)

    def test_has_perm_wrong_user(self, perm_backend, user_2, ref, perm):
        assert not perm_backend.has_perm(user_2, perm, ref)

    def test_get_all_permissions(self, perm_backend, user, object, ref, perm, orphan_perm):
        assert not perm_backend.get_all_permissions(user, object)

        # set reference on object for the following tests
        object.reference = ref
        assert perm_backend.get_all_permissions(user, object) == set(ref.grants.keys())
        assert perm_backend.get_all_permissions(user, ref) == set(ref.grants.keys())
        assert not perm_backend.get_all_permissions(user, orphan_perm)
