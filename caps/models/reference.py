from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Any

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .agent import Agent
from .capability import Capability, CapabilityQuerySet, CanMany
from .capability_set import CapabilitySet
from .nested import NestedBase

__all__ = (
    "ReferenceQuerySet",
    "Reference",
)


class ReferenceBase(NestedBase):
    nested_class = Capability

    @classmethod
    def create_nested_class(cls, new_class, name, attrs={}):
        """Provide `reference` ForeignKey on nested Capability model."""
        return super(ReferenceBase, cls).create_nested_class(
            new_class,
            name,
            {
                "reference": models.ForeignKey(
                    new_class,
                    models.CASCADE,
                    null=True,
                    blank=True,
                    db_index=True,
                    related_name="capabilities",
                    verbose_name=_("Reference"),
                ),
                **attrs,
            },
        )


class ReferenceQuerySet(models.QuerySet):
    """QuerySet for Reference classes."""

    class Meta:
        abstract = True
        unique_together = (("receiver", "target", "emitter"),)

    def emitter(self, agent: Agent | Iterable[Agent]) -> ReferenceQuerySet:
        """References for the provided emitter(s)."""
        if isinstance(agent, Agent):
            return self.filter(Q(origin__receiver=agent) | Q(origin__isnull=True, receiver=agent))
        return self.filter(Q(origin__receiver__in=agent) | Q(origin__isnull=True, receiver__in=agent))

    def receiver(self, agent: Agent | Iterable[Agent]) -> ReferenceQuerySet:
        """References for the provided receiver(s)."""
        if isinstance(agent, Agent):
            return self.filter(receiver=agent)
        return self.filter(receiver__in=agent)

    def ref(self, receiver: Agent | Iterable[Agent] | None, uuid: uuid.UUID) -> ReferenceQuerySet:
        """Reference by uuid and receiver(s).

        Note that ``receiver`` is provided as first parameter in order to enforce its usage. It however can be ``None``: this only
        should be used when queryset has already been filtered by receiver.

        :param receiver: the agent that retrieving the reference.
        :param uuid: the reference uuid to fetch.
        :yield DoesNotExist: when the reference is not found.
        """
        if receiver:
            self = self.receiver(receiver)
        return self.get(uuid=uuid)

    def refs(self, receiver: Agent | Iterable[Agent] | None, uuids: Iterable[uuid.UUID]) -> ReferenceQuerySet:
        """References by many uuid and receiver(s).

        Please refer to :py:meth:`ReferenceQuerySet.ref` for more information.

        :param receiver: the agent that retrieving the reference.
        :param uuids: an iterable of uuids to fetch
        """
        if receiver:
            self = self.receiver(receiver)
        return self.filter(uuid__in=uuids)

    def can(self, permissions: CanMany) -> ReferenceQuerySet:
        """Filter references with the provided permission(s).

        This call :py:meth:`.capability.CapabilityQuerySet.can`, using the same parameters. Providing
        multiple values will make an OR conditional.

        If you want to filter based on AND please use :py:meth:`can_all`.

        :param permissions: permissions to look for
        """
        query = self.model.Capability.objects.can(permissions)
        return self.filter(capabilities__in=query).distinct()

    def can_all(self, permissions: CanMany) -> ReferenceQuerySet:
        """
        Filter references with all the provided permissions.

        :param permissions: permissions to look for, same argument type as :py:meth:`.capability.CapabilityQuerySet.can`.
        """
        return self.filter(self.can_all_q(permissions))

    def can_all_q(self, permissions: CanMany | None) -> Q:
        """Return Q lookup for all permissions."""
        return self.model.Capability.objects.can_all_lookup(
            permissions, "capability__permission__", model=self.model.get_object_class()
        )

    def bulk_create(self, objs, *a, **kw):
        for obj in objs:
            obj.is_valid()
        return super().bulk_create(objs, *a, **kw)

    # TODO: bulk_update -> is_valid()


class Reference(CapabilitySet, models.Model, metaclass=ReferenceBase):
    """Reference are the entry point to access an :py:class:`Object`.

    Reference provides a set of capabilities for specific receiver.
    The concrete sub-model MUST provide the ``target`` foreign key to an
    Object.

    There are two kind of reference:

    - root: the root reference from which all other references to object
      are derived. Created from the :py:meth:`create` class method.
    - derived: reference derived from root or another derived. Created
      from the :py:meth:`derive` method.

    This class enforce fields validation at `save()` and `bulk_create()`.

    Concrete Reference and Capability
    ---------------------------------

    This model is implemented as an abstract in order to have a reference
    specific to each model (see :py:class:`Object` abstract model).

    The related :py:class:`Capability` subclass is created at the same
    time as the concrete implementing reference model. The same mechanism
    also applies on :py:class:`Object` for Reference, as they both use
    base metaclass :py:class:`NestedBase`. They thus can be customized
    if required as this example shows:

    .. code-block:: python

        from caps.models import Reference, Capability

        class MyReference(Reference):
            class Capability(Capability):
                reference = models.ForeignKey(MyReference, models.CASCADE, null=True, related_name="capabilities")
                # custom code here...

            target = models.ForeignKey(MyObject, models.CASCADE)

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
    # target = models.ForeignKey("ConcreteObject", models.CASCADE)
    # """Reference's target."""
    expiration = models.DateTimeField(
        _("Expiration"),
        null=True,
        blank=True,
        help_text=_("Defines an expiration date after which the reference is not longer valid."),
    )

    objects = ReferenceQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = (("origin", "receiver", "target"),)

    @property
    def emitter(self):
        """Agent emitting the reference."""
        return self.origin.receiver if self.origin else self.receiver

    @classmethod
    def get_object_class(cls):
        """Return related Object class."""
        return cls.target.field.related_model

    @classmethod
    def create_root(cls, emitter: Agent, target: object, **kwargs) -> Reference:
        """Create and save a new root reference with provided capabilities."""
        if "origin" in kwargs:
            raise ValueError(
                'attribute "origin" can not be passed as an argument to ' "`create()`: you should use derive instead"
            )
        if target.references.exists():
            raise ValueError(f"A reference already exists for this object.")

        self = cls(receiver=emitter, target=target, **kwargs)
        self.save()

        # clone initial capabilities
        capabilities = list(self.Capability.objects.initials())
        for cap in capabilities:
            cap.reference = self
            cap.pk = None

        self.Capability.objects.bulk_create(capabilities)
        return self

    def is_valid(self, raises: bool = False) -> bool:
        """Check Reference values validity, throwing exception on invalid
        values.

        :returns True if valid, otherwise raise ValueError
        :yield ValueError: when reference is invaldi
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

    def derive(
        self,
        receiver: Agent | int,
        items: CapabilitySet.Caps = None,
        raises: bool = False,
        defaults: dict[str, Any] = {},
        **kwargs,
    ) -> Reference:
        """Create a new reference derived from self.

        :param items: select capabilities to be derived.
        :param raises: raises PermissionDenied error instead of silent it.
        :param defaults: Capability instances' initial arguments.
        :param **kwargs: initial arguments of the new set.
        """
        kwargs = self._get_derived_kwargs(receiver, kwargs)
        obj = type(self).objects.create(**kwargs)
        capabilities = self.derive_caps(items, raises=raises, defaults={**defaults, "reference": obj})
        self.Capability.objects.bulk_create(capabilities)
        return obj

    async def aderive(
        self, items: CapabilitySet.Caps = None, raises: bool = False, defaults: dict[str, Any] = {}, **kwargs
    ) -> Reference:
        """Async version of :py:meth:`derive`."""
        kwargs = self._get_derived_kwargs(kwargs)
        obj = await type(self).objects.acreate(**kwargs)
        capabilities = self.derive_caps(items, raises=raises, defaults={**defaults, "reference": obj})
        await self.Capability.objects.abulk_create(capabilities)
        return obj

    def _get_derived_kwargs(self, receiver: int | Agent, kwargs):
        """Return initial argument for a derived reference from self."""
        r_key = "receiver_id" if isinstance(receiver, int) else "receiver"
        return {
            **kwargs,
            r_key: receiver,
            "depth": self.depth + 1,
            "origin": self,
            "target": self.target,
        }

    def save(self, *a, **kw):
        self.is_valid(raises=True)
        return super().save(*a, **kw)
