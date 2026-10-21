"""
This module provide parent-child objects owned by user(s).

What you'll find here:

    - ChildOwned: owned item with parent child support.
    - OwnedTreeNode: tree like structure handling.

It requires ``oxylus-utils`` package.

"""

from django.core.exceptions import PermissionDenied

from ox_utils.django.models import SaveHook, SaveHookQuerySet, TreeNode, TreeNodeQuerySet

from .owned import Owned, OwnedQuerySet


__all__ = ("ChildOwnedQuerySet", "ChildOwned", "OwnedTreeNodeQuerySet", "OwnedTreeNode")


class ChildOwnedQuerySet(OwnedQuerySet, SaveHookQuerySet):
    """Queryset for :py:class:`ChildOwned`."""

    pass


class ChildOwned(Owned, SaveHook):
    """
    Add parenting mechanism for parent-child relations, checking
    that owner is the same on parent and child.

    Parent and child MUST both inherit from django-caps' ``Owned``.
    """

    parent_attr = "parent"
    """ Field name used for parenting. """

    objects = ChildOwnedQuerySet.as_manager()

    class Meta:
        abstract = True

    def on_save(self, fields=None):
        # we don't set child's owner to parent's one by default in order
        # to avoid bypassing authentication framework.

        parent = getattr(self, self.parent_attr)
        if parent and parent.owner_id != self.owner_id:
            model_name = type(self)._meta.verbose_name.lower()
            raise PermissionDenied(f"Owner of this {model_name} should be the same as its parent")

        super().on_save(fields)


class OwnedTreeNodeQuerySet(ChildOwnedQuerySet, TreeNodeQuerySet):
    pass


class OwnedTreeNode(ChildOwned, TreeNode):
    """
    This combines a :py:class:`TreeNode` with a :py:class:`~.owned.ChildOwned` one.

    It ensures that the owner of the node is the same as its
    parent.
    """

    objects = OwnedTreeNodeQuerySet.as_manager()
    parent_attr = "parent"

    def validate_node(self):
        if self.parent and self.parent.owner_id != self.owner_id:
            label = str(type(self)._meta.verbose_name)
            raise PermissionDenied(f"{label}'s owner must be the same as its parent.")
        super().validate_node()

    class Meta:
        abstract = True
