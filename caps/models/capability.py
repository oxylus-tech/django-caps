from __future__ import annotations
from collections.abc import Iterable
from typing import TypeAlias

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as __

__all__ = ("RawCapability", "RawCapabilities", "Capability")


RawCapability: TypeAlias = tuple[str, int]
""" Serialized representation of a Capability. """

RawCapabilities: TypeAlias = Iterable[RawCapability]
""" Serialized representation of multiple Capability. """


class Capability:
    """A single capability providing permission for executing a single action.

    Derivation
    ----------

    Capability can derived: it means the permission is shared to another agent.
    To be allowed to share, :py:attr:`max_derive` must be greater than 0. When sharing
    only a lower value is allowed to the new capability's field.

    Lets see what it does:

    .. code-block:: python

        from models import MyObject

        permission = Permission.objects.all().first()
        cap = MyObject.Capability(permission=permission, max_derive=2)
        #  `cap` is not saved, we don't core to provide a reference for this example.

        # providing no max_derive defaults to 0
        cap_1 = cap.derive(0)
        assert cap_1.max_derive == 0

        # this raises PermissionDenied
        cap_1.derive()

        # max_derive reduced by 1
        cap_1 = cap.derive()
        assert cap_1.max_derive == 1

        cap_2 = cap_1.derive()
        assert cap_2.max_derive == 0

    **Note:** You'll more work over references for derivation than capabilities themselves.
    """

    permission: str
    """ Permission provided by the capability. """
    max_derive: int = 0
    """ Max allowed derivations (resharing). """

    def __init__(self, permission: str, max_derive: int = 0):
        self.permission = permission
        self.max_derive = max_derive

    @classmethod
    def deserialize(cls, value: RawCapability) -> Capability:
        """Deserialize value from db and return instance."""
        if not isinstance(value[0], str) or not isinstance(value[1], int):
            raise ValueError("Invalid input value")
        return cls(value[0], value[1])

    def serialize(self) -> RawCapability:
        """Return serialized version of self to store in db."""
        return (self.permission, self.max_derive)

    def can_derive(self, max_derive: None | int = None) -> bool:
        """Return True if this capability can be derived."""
        return self.max_derive > 0 and (max_derive is None or max_derive < self.max_derive)

    def derive(self, max_derive: None | int = None, **kwargs) -> Capability:
        """Derive a new capability from self (without checking existence in
        database).

        :param max_derive: when value is None, it will based the value on self's \
                py:attr:`max_derive` minus 1.
        :param **kwargs: extra initial argument of the new Capability
        :return: the new unsaved Capability.

        :yield PermissionDenied: when Capability derivation is not allowed.
        """
        # disallowed values as they are provided by self.
        if "permission" in kwargs:
            raise ValueError("Providing `permission_id` or `permission` is forbidden.")

        if not self.can_derive(max_derive):
            raise PermissionDenied(__("Can not derive capability {}").format(self))
        if max_derive is None:
            max_derive = self.max_derive - 1
        return type(self)(self.permission, max_derive, **kwargs)

    def is_derived(self, capability: Capability = None) -> bool:
        """Return True if `capability` is derived from this one."""
        return self.permission == capability.permission and self.can_derive(capability.max_derive)

    def __str__(self):
        return f'{type(self).__name__}("{self.permission}", {self.max_derive})'

    def __contains__(self, other: Capability):
        """Return True if other `capability` is derived from `self`."""
        return self.is_derived(other)

    def __eq__(self, other: Capability):
        if not isinstance(other, Capability):
            return False
        return self.permission == other.permission and self.max_derive == other.max_derive

    def __hash__(self):
        return hash((self.permission, self.max_derive))
