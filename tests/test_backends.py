import pytest

from caps import backends


@pytest.fixture
def perm_backend():
    return backends.PermissionsBackend()


class TestCapsBackend:
    def test_has_perm(self, perm_backend, user, user_2, object, ref, orphan_perm):
        perm = next(iter(object.root_grants.keys()))
        assert perm_backend.has_perm(user, perm, object)
        assert not perm_backend.has_perm(user, perm)
        assert not perm_backend.has_perm(user_2, perm, object)
        assert not perm_backend.has_perm(user_2, perm)

        # set reference on object for the following tests
        object.reference = ref
        assert perm_backend.has_perm(user_2, perm, object)
        assert perm_backend.has_perm(user_2, perm, ref)
        assert not perm_backend.has_perm(user_2, orphan_perm, object)

    def test_has_perm_wrong_user(self, perm_backend, user_2, object):
        perm = next(iter(object.root_grants.keys()))
        assert not perm_backend.has_perm(user_2, perm, object)

    def test_get_all_permissions(self, perm_backend, user, user_2, object, ref, orphan_perm):
        assert perm_backend.get_all_permissions(user, object)
        assert not perm_backend.get_all_permissions(user_2, object)

        # set reference on object for the following tests
        object.reference = ref
        assert perm_backend.get_all_permissions(user_2, object) == set(ref.grants.keys())
        assert perm_backend.get_all_permissions(user_2, ref) == set(ref.grants.keys())
        assert not perm_backend.get_all_permissions(user_2, orphan_perm)
