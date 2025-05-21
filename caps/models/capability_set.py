from __future__ import annotations
from collections.abc import Iterable

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as __

from .capability import Capability


__all__ = ("CapabilitySet",)


class CapabilitySet:
    """
    Base class to handle set of capabilities. It is one of the bases of :py:class:`Reference`.

    This class should not be used per se.
    """

    capability_class: type[Capability] = Capability
    """ Class used for capabilities. """

    capabilities: Iterable[Capability] = None
    """ Capabilities contained in the CapabilitySet. """

    def is_derived(self, other: CapabilitySet) -> bool:
        """Return True if `capabilities` iterable is a subset of self.

        Set is a subset of another one if and only if:
        - all capabilities of subset are in set and derived from set \
          (cf. `Capability.is_subset`)
        - there is no capability inside subset that are not in set.
        """
        if len(self.capabilities) < len(other.capabilities):
            return False

        capabilities = {c.permission: c for c in self.capabilities}
        for item in other.capabilities:
            capability = capabilities.get(item.permission)
            if not capability or not capability.is_derived(item):
                return False
        return True

    def derive_caps(self, caps: Iterable[Capability] | None = None, raises: bool = False) -> list[Capability]:
        """Derive capabilities from this set.

        When `caps` is provided, it will only derive allowed derivations for declared capabilities.

        When `caps` is not provided, it derives all allowed capabilities of the set.

        The created capabilities are not saved to the db.

        :param source: capabilities to derive
        :param caps: specify which capabilities to derive
        :param raises: if True, raise exception when there are denied derivation.
        :return the list of derived capabilities.
        :yield PermissionDenied: when there are unauthorized derivation and :py:param:`raises` is True.
        """
        if caps is None:
            return [c.derive(0) for c in self.capabilities if c.can_derive(0)]

        by_perm = {c.permission: c for c in self.capabilities}
        denied = []
        for cap in caps:
            capability = by_perm.get(cap.permission)
            try:
                if capability is None or not capability.is_derived(cap):
                    raise PermissionDenied("")
            except PermissionDenied:
                caps.remove(cap)
                denied.append(str(cap))

        if raises and denied:
            raise PermissionDenied(
                __("Some capabilities can not be derived: {denied}").format(denied=", ".join(denied))
            )
        return caps
