from __future__ import annotations

import uuid
from collections.abc import Iterable

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as _

from caps.utils import get_lazy_relation
from .agent import Agent

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

    def expired(self, exclude: bool = False) -> ReferenceQuerySet:
        """Filter by expiration.

        :param exclude: if True, exclude instead of filter.
        """
        q = {"expiration__isnull": False, "expiration__lt": tz.now()}
        return self.exclude(**q) if exclude else self.filter(**q)

    def agent(self, agent: Agent | Iterable[Agent]) -> ReferenceQuerySet:
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


class Reference(models.Model):
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

    uuid = models.UUIDField(_("UUID"), default=uuid.uuid4, db_index=True)
    """Public reference id used in API."""
    origin = models.ForeignKey(
        "self",
        models.CASCADE,
        blank=True,
        null=True,
        related_name="derived",
        verbose_name=_("Source Reference"),
    )
    """Source reference in references chain."""
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
    """ Allowed permissions as a dict of ``{"permission": allowed_reshare}`.

    The integer value of ``allowed_reshare`` determines the amount of reshare can be done.
    """

    objects = ReferenceQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = (("origin", "receiver", "target"),)

    @property
    def is_expired(self):
        """Return True if Reference is expired."""
        return self.expiration is not None and self.expiration <= tz.now()

    @classmethod
    def get_object_class(cls):
        """Return related Object class."""
        return cls.target.field.related_model

    def has_perm(self, user: User, permission: str) -> bool:
        """Return True if reference grants the provided permission."""
        return self.receiver.is_agent(user) and permission in self.grants

    def get_all_permissions(self, user: User) -> set[str]:
        """Return allowed permissions for this user."""
        return self.receiver.is_agent(user) and set(self.grants.keys()) or set()

    def is_valid(self, raises: bool = False) -> bool:
        """Check Reference values validity, throwing exception on invalid
        values.

        :returns True if valid, otherwise raise ValueError
        :yield ValueError: when reference is invaldi
        """
        if self.origin:
            if self.origin.receiver != self.emitter:
                raise ValueError("origin's receiver and self's emitter are different")
        return True

    def share(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs):
        """Create a new saved reference shared from self.

        See :py:meth:`get_shared` for arguments.
        """
        obj = self.get_shared(receiver, grants, **kwargs)
        obj.save()
        return obj

    async def ashare(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs):
        """Create a new saved reference shared from self (async).

        See :py:meth:`get_shared` for arguments.
        """
        obj = self.get_shared(receiver, grants, **kwargs)
        await obj.asave()
        return obj

    def get_shared(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs):
        """Return new reference shared from self. The object is not saved.

        :param receiver: the receiver
        :param grants: optional granted permissions
        :param **kwargs: extra initial arguments
        :yield PermissionDenied: when reference expired or no grant is shareable.
        """
        grants = self.get_shared_grants(grants)
        if not grants:
            raise PermissionDenied("Share not allowed.")
        kwargs = self.get_shared_kwargs(receiver, kwargs)
        return type(self)(grants=grants, **kwargs)

    def get_shared_kwargs(self, receiver: Agent, kwargs):
        """Return initial argument for a derived reference from self."""
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
            "receiver": receiver,
            e_key: emitter,
            "origin": self,
            "target": self.target,
        }

    def get_shared_grants(self, grants: dict[str, int] | None = None, **kwargs) -> dict[str, int]:
        """Return :py:attr:`grants` for shared reference."""
        if grants:
            return {
                key: min(value - 1, grants[key]) for key, value in self.grants.items() if key in grants and value > 0
            }
        return {key: value - 1 for key, value in self.grants.items() if value > 0}

    def get_absolute_url(self):
        return self.target.get_absolute_url()

    def save(self, *a, **kw):
        self.is_valid(raises=True)
        return super().save(*a, **kw)
