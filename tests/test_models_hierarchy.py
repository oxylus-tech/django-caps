import pytest

from django.core.exceptions import PermissionDenied
from tests.app.models import OwnedTreeNode


@pytest.fixture
def owned_root(transactional_db, user_agent):
    return OwnedTreeNode.objects.create(name="owned-root", owner=user_agent)


@pytest.fixture
def owned_child(transactional_db, user_agent, owned_root):
    return OwnedTreeNode.objects.create(name="owned-child", owner=user_agent, parent=owned_root)


class TestOwnedTreeNode:
    def test_validate_node_wrong_owner(self, owned_root, owned_child, user_2_agent):
        with pytest.raises(PermissionDenied):
            owned_child.owner = user_2_agent
            owned_child.validate_node()

    def test_validate_node_ok(self, owned_root, owned_child):
        owned_child.validate_node()
