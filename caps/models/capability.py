from __future__ import annotations
import functools
import operator
from collections.abc import Iterable

from asgiref.sync import sync_to_async
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import gettext as __
from django.utils.translation import gettext_lazy as _

__all__ = ("CapabilityQuerySet", "Capability")


class CapabilityQuerySet(models.QuerySet):
    def _get_items_queryset(self, items: "Iterable[Capability]") -> models.QuerySet:
        """Get or create capabilities from database."""
        q_objects = (Q(name=r.name, max_derive=r.max_derive) for r in items)
        query = functools.reduce(operator.or_, q_objects)
        return self.filter(query)

    def get_or_create_many(self, items: Iterable[Capability]) -> models.Queryset:
        """Retrieve capabilities from database, create it if missing.

        Subset's items are updated.
        """
        if not items:
            return self.none()

        queryset = self._get_items_queryset(items)
        # force queryset to use a different cache, in order to return it
        # unevaluated
        names = {r.name for r in queryset.all()}
        missing = (item for item in items if item.name not in names)
        with transaction.atomic(queryset.db):
            Capability.objects.bulk_create(missing)
        return queryset

    # FIXME: awaits for django.transaction async support
    async def aget_or_create_many(self, items: Iterable[Capability]) -> models.Queryset:
        """Async version of `get_or_create_many`."""
        func = sync_to_async(self.get_or_create_many)
        return await func(items)


class Capability(models.Model):
    """A single capability.

    Provide permission for a specific action. Capability are stored as unique for each action/max_derive couple.
    """

    IntoValue: tuple[str, str] | list[str] | Capability | str
    """Value types from which capability can be created from using class method
    `into()`."""

    name = models.CharField(_("Action"), max_length=32, db_index=True)
    max_derive = models.PositiveIntegerField(_("Maximum Derivation"), default=0)

    objects = CapabilityQuerySet.as_manager()

    class Meta:
        unique_together = (("name", "max_derive"),)

    @staticmethod
    def get_name(model, action):
        """Return capability name for a specific model and action."""
        return model._meta.db_alias + "_" + action

    @classmethod
    def into(cls, value: Capability.IntoValue):
        """Return a Capability based on value.

        Value formats: `name`, `(name, max_derive)`, `Capability`
        (returned as is in this case)
        """
        if isinstance(value, (list, tuple)):
            return cls(name=value[0], max_derive=value[1])
        if isinstance(value, Capability):
            return value
        if isinstance(value, str):
            return cls(name=value, max_derive=0)
        raise NotImplementedError("Provided values are not supported")

    def can_derive(self, max_derive: None | int = None) -> bool:
        """Return True if this capability can be derived."""
        return self.max_derive > 0 and (max_derive is None or max_derive < self.max_derive)

    def derive(self, max_derive: None | int = None) -> Capability:
        """Derive a new capability from self (without checking existence in
        database)."""
        if not self.can_derive(max_derive):
            raise PermissionDenied(__("can not derive capability {name}").format(name=self.name))
        if max_derive is None:
            max_derive = self.max_derive - 1
        return Capability(name=self.name, max_derive=max_derive)

    def is_derived(self, capability: Capability = None) -> bool:
        """Return True if `capability` is derived from this one."""
        return self.name == capability.name and self.can_derive(capability.max_derive)

    def __str__(self):
        return 'Capability(pk={}, name="{}", max_derive={})'.format(self.pk, self.name, self.max_derive)

    def __contains__(self, other: Capability):
        """Return True if other `capability` is derived from `self`."""
        return self.is_derived(other)

    def __eq__(self, other: Capability):
        if not isinstance(other, Capability):
            return False
        if self.pk and other.pk:
            return self.pk == other.pk
        return self.name == other.name and self.max_derive == other.max_derive
