from __future__ import annotations
from collections.abc import Iterable

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as __

from .capability import Capability

__all__ = ("BaseCapabilitySet", "CapabilitySet")


class BaseCapabilitySet:
    """Base class to handle set of capabilities."""

    DeriveItems: Capability.IntoValue
    """Type from which set can be derived from."""
    capabilities: Iterable[Capability] = None

    def get_capabilities(self) -> Iterable[Capability]:
        return self.capabilities

    # TODO: test
    def get_capability(self, name: str) -> Capability | None:
        """Get capability by name or None."""
        return next((r for r in self.get_capabilities() if r.name == name), None)

    def is_derived(self, other: BaseCapabilitySet) -> bool:
        """Return True if `capabilities` iterable is a subset of self.

        Set is a subset of another one if and only if:
        - all capabilities of subset are in set and derived from set \
          (cf. `Capability.is_subset`)
        - there is no capability inside subset that are not in set.
        """
        items = other.get_capabilities()
        capabilities = {c.name: c for c in self.get_capabilities()}
        for item in items:
            capability = capabilities.get(item.name)
            if not capability or not capability.is_derived(item):
                return False
        return True

    def derive_caps(self, items: BaseCapabilitySet.DeriveItems = None) -> list[Capability]:
        """Derive all capabilities from this set using provided optionnal
        iterator.

        If `items` is not provided, derive capabilities from self, without
        allowing them to be shared.
        :return an array of saved Capability instances.
        """
        if items is None:
            items = [r.derive(max_derive=0) for r in self.get_capabilities() if r.can_derive(0)]
        else:
            items = self._derive_caps(self.get_capabilities(), items)
        return Capability.objects.get_or_create_many(items) if items else None

    # async def aderive_caps(self, items: DeriveItems = None)
    #       -> list[Capability]:
    #     """
    #     Async version of `derive_caps`.
    #     """
    #     if items is None:
    #         items = [r.derive(max_derive=0) for r in self.get_capabilities()
    #                  if r.can_derive(0)]
    #     else:
    #         items = self._derive_caps(self.get_capabilities(), items)
    #     return Capability.objects.get_or_create_many(items)

    def _derive_caps(self, source: Iterable[Capability], items: BaseCapabilitySet.DeriveItems) -> list[Capability]:
        """Derive capabilities using given dict of parents."""
        by_name = {r.name: r for r in source}
        derived, denied = [], []
        for item in items:
            item = Capability.into(item)
            capability = by_name.get(item.name)
            if not capability or not capability.is_derived(item):
                denied.append(item.name)
            else:
                derived.append(item)

        if denied:
            raise PermissionDenied(
                __("Some capabilities can not be derived: {denied}").format(denied=", ".join(denied))
            )
        return derived


class CapabilitySet(BaseCapabilitySet):
    def __init__(self, capabilities: Iterable[Capability]):
        self.capabilities = capabilities and list(capabilities) or []

    def derive(self, items: BaseCapabilitySet.DeriveItems = None, **init_kwargs) -> CapabilitySet:
        """Derive this `CapabilitySet` from `self`.

        Dont save new capabilities of new subset.
        """
        capabilities = self.derive_caps(items)
        # capabilities = Capability.objects.bulk_create_many(capabilities)
        return type(self)(capabilities, **init_kwargs)

    async def aderive(self, items: Capability.DeriveItems = None, **init_kwargs) -> CapabilitySet:
        """Async version of `derive`."""
        capabilities = await self.aderive_caps(items)
        # capabilities = await Capability.objects \
        #                                .abulk_create_many(capabilities)
        # capabilities = (r async for r in capabilities)
        return type(self)(capabilities, **init_kwargs)
