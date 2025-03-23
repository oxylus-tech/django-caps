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
    """A single capability providing authorization for executing a single action.

    Capability can be derived a certain amount of times, which is specified by
    :py:attr:`max_derive`. When this value is not specified (for exemple when
    :py:meth:`derive` or :py:meth:`into`), it is always defaulted to 0 (thus disallowing
    any further derivation).

    Lets see what it does:

    .. code-block:: python

        cap = Capability(name="read", max_derive=2)

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
    

    Capability are stored as unique for each action/max_derive pair. When requiring
    to create multiple capabilities, one should use queryset's
    :py:meth:`~CapabilityQuerySet.get_or_create_many`.
    """

    IntoValue: tuple[str, int] | Capability | str
    """Value types from which capability can be created from using class method
    `into()`."""

    name = models.CharField(_("Action"), max_length=32, db_index=True)
    """ Action programmatic name. """
    max_derive = models.PositiveIntegerField(_("Maximum Derivation"), default=0)
    """ Maximum allowed derivations. """

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
        if isinstance(value, tuple):
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
        database).

        :param max_derive: when value is None, it will based the value on self's \
                py:attr:`max_derive` minus 1.
        :return the new unsaved Capability.
        :yield PermissionDenied: when Capability derivation is not allowed.
        """
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
