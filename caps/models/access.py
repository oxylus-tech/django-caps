from __future__ import annotations

import uuid
from collections.abc import Iterable

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone as tz
from django.utils.translation import gettext_lazy as _

from caps.utils import get_lazy_relation
from .agent import Agent

__all__ = (
    "AccessQuerySet",
    "Access",
)


class AccessQuerySet(models.QuerySet):
    """QuerySet for Access classes."""

    def available(self, agent: Agent | Iterable[Agent] | None = None) -> AccessQuerySet:
        """Return available accesses based on expiration and eventual user."""
        if agent is not None:
            self = self.agent(agent)
        return self.filter(Q(expiration__isnull=True) | Q(expiration__gt=tz.now()))

    def expired(self, exclude: bool = False) -> AccessQuerySet:
        """Filter by expiration.

        :param exclude: if True, exclude instead of filter.
        """
        q = {"expiration__isnull": False, "expiration__lt": tz.now()}
        return self.exclude(**q) if exclude else self.filter(**q)

    def agent(self, agent: Agent | Iterable[Agent]) -> AccessQuerySet:
        """
        Filter accesses that agent is either receiver or
        emitter..
        """
        if isinstance(agent, Agent):
            return self.filter(Q(emitter=agent) | Q(receiver=agent))
        return self.filter(Q(emitter__in=agent) | Q(receiver__in=agent))

    def emitter(self, agent: Agent | Iterable[Agent]) -> AccessQuerySet:
        """Accesss for the provided emitter(s)."""
        if isinstance(agent, Agent):
            return self.filter(emitter=agent)
        return self.filter(emitter__in=agent)

    def receiver(self, agent: Agent | Iterable[Agent]) -> AccessQuerySet:
        """Accesss for the provided receiver(s)."""
        if isinstance(agent, Agent):
            return self.filter(receiver=agent)
        return self.filter(receiver__in=agent)

    def access(self, receiver: Agent | Iterable[Agent] | None, uuid: uuid.UUID) -> AccessQuerySet:
        """Access by uuid and receiver(s).

        Note that ``receiver`` is provided as first parameter in order to enforce its usage. It however can be ``None``: this only
        should be used when queryset has already been filtered by receiver.

        :param receiver: the agent that retrieving the access.
        :param uuid: the access uuid to fetch.
        :yield DoesNotExist: when the access is not found.
        """
        if receiver:
            self = self.receiver(receiver)
        return self.get(uuid=uuid)

    def accesses(self, receiver: Agent | Iterable[Agent] | None, uuids: Iterable[uuid.UUID]) -> AccessQuerySet:
        """Accesss by many uuid and receiver(s).

        Please accesser to :py:meth:`AccessQuerySet.access` for more information.

        :param receiver: the agent that retrieving the access.
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


class Access(models.Model):
    """Access are the entry point to access an :py:class:`Owned`.

    Access provides a set of capabilities for specific receiver.
    The concrete sub-model MUST provide the ``target`` foreign key to an
    Owned.

    There are two kind of access:

    - root: the root access from which all other accesses to object
      are derived. Created from the :py:meth:`create` class method. It has no :py:attr:`origin`
      and **there can be only one root access per :py:class:`Owned` instance**.
    - derived: access derived from root or another derived. Created
      from the :py:meth:`derive` method.

    This class enforce fields validation at `save()` and `bulk_create()`.

    Concrete Access
    ------------------

    This model is implemented as an abstract in order to have a access
    specific to each model (see :py:class:`Owned` abstract model). The
    actual concrete class is created when :py:class:`Owned` is subclassed
    by a concrete model.
    """

    uuid = models.UUIDField(_("Id"), default=uuid.uuid4, db_index=True)
    """Public access id used in API."""
    origin = models.ForeignKey(
        "self",
        models.CASCADE,
        blank=True,
        null=True,
        related_name="derived",
        verbose_name=_("Origin"),
    )
    """Source access in accesses chain."""
    emitter = models.ForeignKey(Agent, models.CASCADE, verbose_name=_("Emitter"), related_name="+", db_index=True)
    """Agent receiving capability."""
    receiver = models.ForeignKey(Agent, models.CASCADE, verbose_name=_("Receiver"), related_name="+", db_index=True)
    """Agent receiving capability."""
    expiration = models.DateTimeField(
        _("Expiration"),
        null=True,
        blank=True,
        help_text=_("Defines an expiration date after which the access is not longer valid."),
    )
    """Date of expiration."""
    grants = models.JSONField(_("Granted permissions"), blank=True)
    """ Allowed permissions as a dict of ``{"permission": allowed_reshare}``.

    The integer value of ``allowed_reshare`` determines the amount of reshare can be done.
    """

    objects = AccessQuerySet.as_manager()

    class Meta:
        abstract = True
        verbose_name = _("Access")
        verbose_name_plural = _("Accesses")
        unique_together = (("origin", "receiver", "target"),)

    @property
    def is_expired(self):
        """Return True if Access is expired."""
        return self.expiration is not None and self.expiration <= tz.now()

    @classmethod
    def get_object_class(cls):
        """Return related Owned class."""
        return cls.target.field.related_model

    def has_perm(self, user: User, permission: str) -> bool:
        """Return True if access grants the provided permission."""
        return self.receiver.is_agent(user) and permission in self.grants

    def get_all_permissions(self, user: User) -> set[str]:
        """Return allowed permissions for this user."""
        return self.receiver.is_agent(user) and set(self.grants.keys()) or set()

    def is_valid(self, raises: bool = False) -> bool:
        """Check Access values validity, throwing exception on invalid
        values.

        :returns True if valid, otherwise raise ValueError
        :yield ValueError: when access is invaldi
        """
        if self.origin:
            if self.origin.receiver != self.emitter:
                raise ValueError("origin's receiver and self's emitter are different")
        return True

    def share(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs):
        """Create a new saved access shared from self.

        See :py:meth:`get_share` for arguments.
        """
        obj = self.get_share(receiver, grants, **kwargs)
        obj.save()
        return obj

    async def ashare(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs):
        """Create a new saved access shared from self (async).

        See :py:meth:`get_share` for arguments.
        """
        obj = self.get_share(receiver, grants, **kwargs)
        await obj.asave()
        return obj

    def get_share(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs):
        """Return new access shared from self. The object is not saved.

        :param receiver: the receiver
        :param grants: optional granted permissions
        :param **kwargs: extra initial arguments
        :yield PermissionDenied: when access expired or no grant is shareable.
        """
        grants = self.get_share_grants(grants)
        if not grants:
            raise PermissionDenied("Share not allowed.")
        kwargs = self.get_share_kwargs(receiver, kwargs)
        return type(self)(grants=grants, **kwargs)

    def get_share_kwargs(self, receiver: Agent, kwargs):
        """Return initial argument for a derived access from self."""
        e_key, emitter = get_lazy_relation(self, "receiver", "emitter")

        if self.expiration:
            if self.is_expired:
                raise PermissionDenied("Access is expired.")

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

    def get_share_grants(self, grants: dict[str, int] | None = None, **kwargs) -> dict[str, int]:
        """Return :py:attr:`grants` for shared access."""
        if grants:
            return {
                key: min(value - 1, grants[key]) for key, value in self.grants.items() if key in grants and value > 0
            }
        return {key: value - 1 for key, value in self.grants.items() if value > 0}

    def get_absolute_url(self):
        if not self.target.detail_url_name:
            raise ValueError("Missing attribute `detail_url_name`.")

        return reverse(self.target.detail_url_name, kwargs={"uuid": self.uuid})

    def save(self, *a, **kw):
        self.is_valid(raises=True)
        return super().save(*a, **kw)

    def __str__(self):
        return f"{self.emitter} -> {self.receiver}, {self.target.uuid}"
