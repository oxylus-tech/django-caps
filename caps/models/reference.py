from __future__ import annotations

import uuid
from collections.abc import Iterable

from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.translation import gettext_lazy as _

from .agent import Agent
from .capability import Capability, CapabilityQuerySet
from .capability_set import BaseCapabilitySet

__all__ = (
    "ReferenceQuerySet",
    "Reference",
)


class ReferenceQuerySet(models.QuerySet):
    """QuerySet for Reference classes."""

    class Meta:
        abstract = True
        unique_together = (("receiver", "target", "emitter"),)

    def emitter(self, agent: Agent | Iterable[Agent]) -> ReferenceQuerySet:
        """References for the provided emitter(s)."""
        if isinstance(agent, Agent):
            return self.filter(origin__receiver=agent)
        return self.filter(origin__receiver__in=agent)

    def receiver(self, agent: Agent | Iterable[Agent]) -> ReferenceQuerySet:
        """References for the provided receiver(s)."""
        if isinstance(agent, Agent):
            return self.filter(receiver=agent)
        return self.filter(receiver__in=agent)

    def ref(self, receiver: Agent | Iterable[Agent], uuid: uuid.UUID) -> ReferenceQuerySet:
        """Reference by uuid and receiver(s).

        :yield DoesNotExist: when the reference is not found.
        """
        return self.receiver(receiver).get(uuid=uuid)

    def refs(self, receiver: Agent | Iterable[Agent], uuids: Iterable[uuid.UUID]) -> ReferenceQuerySet:
        """References by many uuid and receiver(s)."""
        return self.receiver(receiver).filter(uuid__in=uuids)

    def action(self, name: str) -> ReferenceQuerySet:
        return self.filter(capabilities__name=name)

    def actions(self, names: Iterable[str]) -> ReferenceQuerySet:
        return self.filter(capabilities__name__in=names)

    def bulk_create(self, objs, *a, **kw):
        for obj in objs:
            obj.is_valid()
        return super().bulk_create(objs, *a, **kw)

    # TODO: bulk_update -> is_valid()


# TODO:
# - merge existing references
class Reference(BaseCapabilitySet, models.Model):
    """Reference are set of capabilities targeting a specific object. There are two kind of reference:

    - root: the root reference from which all other references to object
      are derived. Created from the `create()` class method.
    - derived: reference derived from root or another derived. Created
      from the `derive()` class method.

    This class enforce fields validation at `save()` and `bulk_create()`.

    This model is implemented as an abstract in order to have a reference
    specific to each model (see `Object` abstract model).
    """

    uuid = models.UUIDField(_("Reference"), default=uuid.uuid4, db_index=True)
    """Public reference used in API and with the external world."""
    origin = models.ForeignKey(
        "self",
        models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("Source Reference"),
    )
    """Source reference in references chain."""
    depth = models.PositiveIntegerField(
        _("Share Count"), default=0, help_text=_("The amount of time a reference can be re-shared.")
    )
    """Reference chain's current depth."""
    receiver = models.ForeignKey(Agent, models.CASCADE)
    """Agent receiving capability."""
    target = models.ForeignKey("ConcreteObject", models.CASCADE)
    """Reference's target."""
    capabilities = models.ManyToManyField(Capability, verbose_name=_("Capability"))

    objects = ReferenceQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = (("origin", "receiver", "target"),)

    @property
    def emitter(self):
        """Agent emitting the reference."""
        return self.origin.receiver if self.origin else self.receiver

    @classmethod
    def create(
        cls,
        emitter: Agent,
        target: object,
        capabilities: Iterable[Capability],
        **kw,
    ) -> Reference:
        """Create and save a new root reference with provided capabilities."""
        if "origin" in kw:
            raise ValueError(
                'attribute "origin" can not be passed as an argument to ' "`create()`: you should use derive instead"
            )

        self = cls(receiver=emitter, target=target, **kw)
        self.save()
        self.capabilities.add(*capabilities)
        return self

    def is_valid(self, raises: bool = False) -> bool:
        """Check Reference values validity, throwing exception on invalid
        values.

        :returns True if valid, otherwise raise ValueError
        """
        if self.origin:
            # if self.origin.receiver != self.emitter:
            #    raise ValueError("origin's receiver and self's emitter are "
            #                     "different")
            if self.origin.depth >= self.depth:
                if raises:
                    raise ValueError("origin's depth is higher than self's")
                else:
                    return False
        return True

    def is_derived(self, other: Reference) -> bool:
        if other.depth <= self.depth or self.target != other.target:
            return False
        return super().is_derived(other)

    def get_capabilities(self) -> CapabilityQuerySet:
        return self.capabilities.all()

    def can(self, action: str|list[str], raises=False) -> bool:
        """
        Return wether an action is allowed.

        :param action: action(s) to check on
        :param raises: raise PermissionDenied instead of returning False
        :yield PermissionDenied: action is not allowed.
        """
        kw = {"name": action} if isinstance(action, str) else {"name__in": action}
        if not self.capabilities.filter(**kw).exists():
            if raises:
                raise PermissionDenied(f"{action} is not allowed")
            return False
        return True

    def derive(
        self,
        receiver: Agent,
        items: BaseCapabilitySet.DeriveItems = None,
        update: bool = False,
    ) -> Reference:
        """Derive this `CapabilitySet` from `self`.

        :param Agent receiver: receiver of the new reference
        :param DeriveItems items: if provided, only derive those capabilities
        :param bool update: update existing reference if it exists
        """
        subset = None
        if update:
            queryset = self.objects.filter(origin=self, receiver=receiver, target=self.target)
            subset = queryset.first()

        capabilities = self.derive_caps(items)
        if subset is None:
            subset = type(self)(
                origin=self,
                depth=self.depth + 1,
                receiver=receiver,
                target=self.target,
            )
        subset.save()
        subset.capabilities.add(*capabilities)
        return subset

    def save(self, *a, **kw):
        self.is_valid(raises=True)
        return super().save(*a, **kw)
