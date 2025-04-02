from __future__ import annotations
from collections.abc import Iterable
from typing import Any

from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from django.utils.translation import gettext as __

from .capability import Capability

__all__ = ("CapabilitySet",)


class CapabilitySet:
    """Base class to handle set of capabilities.

    This class should not be used per se.
    """

    Capability: type[Capability] | Permission
    """Capability class to use. It must be set in order to use CapabilitySet. """
    Cap: int | tuple[int, int]
    """
    Capability information, as tuple of ``(permission_id, max_derive)`` or single permission
    id (then ``max_derive is None``).
    """
    Caps: Iterable[CapabilitySet.Cap]
    """ Many capability information. """
    capabilities: Iterable[Capability] = None
    """ Capabilities contained in the CapabilitySet. """

    def get_capabilities(self) -> Iterable[Capability]:
        return self.capabilities

    # FIXME: remove?
    def get_capability(self, codename: str) -> Capability | None:
        """Get capability by name or None."""
        return next((r for r in self.get_capabilities() if r.codename == codename), None)

    def is_derived(self, other: CapabilitySet) -> bool:
        """Return True if `capabilities` iterable is a subset of self.

        Set is a subset of another one if and only if:
        - all capabilities of subset are in set and derived from set \
          (cf. `Capability.is_subset`)
        - there is no capability inside subset that are not in set.
        """
        capabilities = {c.permission_id: c for c in self.get_capabilities()}
        for item in other.get_capabilities():
            capability = capabilities.get(item.permission_id)
            if not capability or not capability.is_derived(item):
                return False
        return True

    def create_capability(self, cap: CapabilitySet.Cap, **kwargs) -> CapabilitySet.Capability:
        """Create a single (unsaved) capability.

        :param cap: capability information
        :param **kwargs: extra initial arguments
        :return the new unsaved capability instance.
        """
        perm_id, kwargs = self.get_capability_kwargs(cap, {**kwargs, "reference": self})
        return self.Capability(permission_id=perm_id, **kwargs)

    def create_capabilities(self, caps: CapabilitySet.Caps, **kwargs) -> list[CapabilitySet.Capability]:
        """Create multiple capabilities based on descriptors.

        :param caps: capabilities' informations
        :param **kwargs: extra initial arguments
        :return a list of unsaved capabilities instances.
        """
        return [self.create_capability(cap, **kwargs) for cap in caps]

    def derive_caps(
        self, caps: CapabilitySet.Caps | None = None, raises: bool = False, defaults: dict[str, Any] = {}
    ) -> list[Capability]:
        """Derive capabilities from this set.

        When `caps` is provided, it will only derive allowed derivations for declared capabilities.

        When `caps` is not provided, it derives all allowed capabilities of the set.

        The created capabilities are not saved to the db.

        :param source: capabilities to derive
        :param caps: specify which capabilities to derive
        :param raises: if True, raise exception when there are denied derivation.
        :param defaults: initial arguments to pass to all generated capabilities.
        :return the list of derived capabilities.
        :yield PermissionDenied: when there are unauthorized derivation and :py:param:`raises` is True.
        """
        if caps is None:
            defaults = {"max_derive": 0, **defaults}
            return [c.derive(**defaults) for c in self.get_capabilities() if c.can_derive(defaults["max_derive"])]

        by_perm = {c.permission_id: c for c in self.get_capabilities()}
        derived, denied = [], []
        for cap in caps:
            perm_id, kwargs = self.get_capability_kwargs(cap, defaults)
            capability = by_perm.get(perm_id)
            try:
                if capability is None:
                    raise PermissionDenied("")

                # we always use Capability.derive in order to ensure custom
                # implementations.
                obj = capability.derive(**kwargs)
                derived.append(obj)
            except PermissionDenied:
                denied.append(str(cap))

        if raises and denied:
            raise PermissionDenied(
                __("Some capabilities can not be derived: {denied}").format(denied=", ".join(denied))
            )
        return derived

    def get_capability_kwargs(self, cap: CapabilitySet.Cap, defaults: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """
        From provided ``cap`` description, return a tuple with permission id and :py:meth:`Capability.derive` arguments.

        We return a tuple because permission id can not be provided
        to the derive method.

        :param cap: the capability descriptor;
        :param **kwargs: extra arguments to pass down to the method;
        """
        if isinstance(cap, tuple):
            perm_id, max_derive = cap
        elif isinstance(cap, int):
            perm_id, max_derive = cap, None
        else:
            raise ValueError(f"Invalid value for `cap`: {cap}")
        return perm_id, {"max_derive": max_derive, **defaults}
