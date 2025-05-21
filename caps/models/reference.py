from __future__ import annotations

import uuid
from collections.abc import Iterable
from functools import cached_property

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as _

from caps.utils import get_lazy_relation
from .agent import Agent
from .capability import Capability
from .capability_set import CapabilitySet

__all__ = (
    "ReferenceQuerySet",
    "Reference",
)


class ReferenceQuerySet(models.QuerySet):
    """QuerySet for Reference classes."""

    class Meta:
        abstract = True
        unique_together = (("receiver", "target", "emitter"),)

    def available(self, agent: Agent | Iterable[Agent] | None = None) -> ReferenceQuerySet:
        """Return available references based on expiration and eventual user."""
        if agent is not None:
            self = self.agent(agent)
        return self.filter(Q(expiration__isnull=True) | Q(expiration__gt=tz.now()))

    def agent(self, agent: Agent | Iterable[Agent]):
        """
        Filter references that agent is either receiver or
        emitter..
        """
        if isinstance(agent, Agent):
            return self.filter(Q(emitter=agent) | Q(receiver=agent))
        return self.filter(Q(emitter__in=agent) | Q(receiver__in=agent))

    def emitter(self, agent: Agent | Iterable[Agent]) -> ReferenceQuerySet:
        """References for the provided emitter(s)."""
        if isinstance(agent, Agent):
            return self.filter(emitter=agent)
        return self.filter(emitter__in=agent)

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

    def bulk_create(self, objs, *a, **kw):
        """Check that objects are valid when saving models in bulk."""
        for obj in objs:
            obj.is_valid()
        return super().bulk_create(objs, *a, **kw)

    # TODO: bulk_update -> is_valid()


class Reference(CapabilitySet, models.Model):
    """Reference are the entry point to access an :py:class:`Object`.

    Reference provides a set of capabilities for specific receiver.
    The concrete sub-model MUST provide the ``target`` foreign key to an
    Object.

    There are two kind of reference:

    - root: the root reference from which all other references to object
      are derived. Created from the :py:meth:`create` class method. It has no :py:attr:`origin`
      and **there can be only one root reference per :py:class:`Object` instance.
    - derived: reference derived from root or another derived. Created
      from the :py:meth:`derive` method.

    This class enforce fields validation at `save()` and `bulk_create()`.

    Concrete Reference
    ------------------

    This model is implemented as an abstract in order to have a reference
    specific to each model (see :py:class:`Object` abstract model). The
    actual concrete class is created when :py:class:`Object` is subclassed
    by a concrete model.
    """

    uuid = models.UUIDField(_("Reference"), default=uuid.uuid4, db_index=True)
    """Public reference used in API and with the external world."""
    origin = models.ForeignKey(
        "self",
        models.CASCADE,
        blank=True,
        null=True,
        related_name="derived",
        verbose_name=_("Source Reference"),
    )
    """Source reference in references chain."""
    depth = models.PositiveIntegerField(
        _("Share limit"), default=0, help_text=_("The amount of time a reference can be re-shared.")
    )
    """Reference chain's current depth."""
    emitter = models.ForeignKey(
        Agent, models.CASCADE, verbose_name=_("Emitter"), related_name="emit_references", db_index=True
    )
    """Agent receiving capability."""
    receiver = models.ForeignKey(
        Agent, models.CASCADE, verbose_name=_("Receiver"), related_name="references", db_index=True
    )
    """Agent receiving capability."""
    expiration = models.DateTimeField(
        _("Expiration"),
        null=True,
        blank=True,
        help_text=_("Defines an expiration date after which the reference is not longer valid."),
    )
    """Date of expiration."""
    grants = models.JSONField(_("Granted capabilities"), blank=True)
    """ Allowed capabilities as DB field.

    This is stored as a dict where keys are permission codename and
    value `max_derive` argument (or second argument of Capability
    constructor).
    """

    objects = ReferenceQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = (("origin", "receiver", "target"),)

    @property
    def is_expired(self):
        """Return True if Reference is expired."""
        return self.expiration is not None and self.expiration <= tz.now()

    @cached_property
    def capabilities(self) -> list[Capability]:
        """Self' capabilities as list of Capability instances."""
        return [self.capability_class.deserialize(val) for val in self.grants.items()]

    @classmethod
    def get_object_class(cls):
        """Return related Object class."""
        return cls.target.field.related_model

    @classmethod
    def create_root(cls, emitter: Agent, target: object, template: Reference | None = None, **kwargs) -> Reference:
        """Create and save a new root reference.

        There can be only one root reference per object.

        New capabilities will be created by cloning default ones (which are those without an assigned reference).

        :param emitter: the owner of the object, as it is emitter of the root reference.
        :param target: target :py:class:`.object.Object` instance.
        :param template: use this reference instance as template instead of default one.
        :param **kwargs: Reference's initial arguments.
        :return: the created root reference.
        :yield ValueError: when ``origin`` is provided or a root reference already exists.
        """
        if "origin" in kwargs:
            raise ValueError(
                'attribute "origin" can not be passed as an argument to ' "`create()`: you should use derive instead"
            )
        if target.references.exists():
            raise ValueError("A reference already exists for this object.")

        kwargs["grants"] = dict(cls.get_object_class().root_reference_grants)
        return cls.objects.create(emitter=emitter, receiver=emitter, target=target, **kwargs)

    def has_perm(self, user: User, permission: str) -> bool:
        """Return True if reference grants the provided permission."""
        return self.receiver.is_agent(user) and permission in self.grants

    def get_all_permissions(self, user: User) -> bool:
        """Return allowed permissions for this user."""
        return self.receiver.is_agent(user) and set(self.grants.keys()) or []

    def is_valid(self, raises: bool = False) -> bool:
        """Check Reference values validity, throwing exception on invalid
        values.

        :returns True if valid, otherwise raise ValueError
        :yield ValueError: when reference is invaldi
        """
        if self.origin:
            # FIXME
            if self.origin.receiver != self.emitter:
                raise ValueError("origin's receiver and self's emitter are different")
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

    def derive(
        self, receiver: Agent | int, capabilities: Iterable[Capability] | None = None, raises: bool = False, **kwargs
    ) -> Reference:
        """Create a new reference derived from self.

        :param receiver: the reference's receiver
        :param capabilities: select capabilities to be derived.
        :param raises: raises PermissionDenied error instead of silent it.
        :param **kwargs: initial arguments of the Reference.
        """
        kwargs = self._get_derive_kwargs(receiver, kwargs)
        capabilities = self.derive_caps(capabilities, raises)
        kwargs["grants"] = dict(cap.serialize() for cap in capabilities)
        return type(self).objects.create(**kwargs)

    async def aderive(
        self, receiver: Agent | int, capabilities: Iterable[Capability] | None = None, raises: bool = False, **kwargs
    ) -> Reference:
        """Async version of :py:meth:`derive`."""
        kwargs = self._get_derive_kwargs(receiver, kwargs)
        capabilities = self.derive_caps(capabilities, raises)
        kwargs["grants"] = dict(cap.serialize() for cap in capabilities)
        return await type(self).objects.acreate(**kwargs)

    def _get_derive_kwargs(self, receiver: int | Agent, kwargs):
        """Return initial argument for a derived reference from self."""
        r_key = "receiver_id" if isinstance(receiver, int) else "receiver"
        e_key, emitter = get_lazy_relation(self, "receiver", "emitter")

        if self.expiration:
            if self.is_expired:
                raise PermissionDenied("Reference is expired.")

            if expiration := kwargs.get("expiration"):
                kwargs["expiration"] = min(expiration, self.expiration)
            else:
                kwargs["expiration"] = self.expiration

        return {
            **kwargs,
            r_key: receiver,
            e_key: emitter,
            "depth": self.depth + 1,
            "origin": self,
            "target": self.target,
        }

    def get_absolute_url(self) -> str:
        """
        Return url to the related object.

        :yield ValueError: when related object class has no `detail_url_name` provided.
        """
        url_name = self.target.detail_url_name
        if not url_name:
            raise ValueError("Missing attribute `detail_url_name` on target object.")
        return reverse(url_name, kwargs={"uuid": self.uuid})

    def save(self, *a, **kw):
        self.is_valid(raises=True)
        return super().save(*a, **kw)
