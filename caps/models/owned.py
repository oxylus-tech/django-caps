from __future__ import annotations
from uuid import uuid4
from typing import Iterable

from django.db import models
from django.db.models import Q, OuterRef, Prefetch, Subquery
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from .agent import Agent
from .access import Access, AccessQuerySet
from .nested import NestedModelBase

__all__ = ("OwnedBase", "OwnedQuerySet", "Owned")


class OwnedBase(NestedModelBase):
    """Metaclass for Owned model classes.

    It subclass Access if no `Access` member is provided.
    """

    nested_class = Access

    @classmethod
    def create_nested_class(cls, new_class, name, attrs={}):
        """Provide `target` ForeignKey on nested Access model."""
        return super(OwnedBase, cls).create_nested_class(
            new_class,
            name,
            {
                "target": models.ForeignKey(
                    new_class,
                    models.CASCADE,
                    db_index=True,
                    related_name="accesses",
                    verbose_name=_("Target"),
                ),
                **attrs,
            },
        )


class OwnedQuerySet(models.QuerySet):
    """QuerySet for Owneds."""

    def available(self, agents: Agent | Iterable[Agent], accesses: AccessQuerySet | None = None):
        """
        Return object available to provided agents as owner or receiver (when ``accesses`` is provided).

        It prefetch/annotates the resulting items using :py:meth:`access`, if accesses is provided.

        :param agents: for the provided agent
        :param accesses: use this queryset for accesses
        """
        if accesses is None or accesses.query.is_empty():
            if isinstance(agents, Agent):
                return self.filter(owner=agents)
            return self.filter(owner__in=agents)

        accesses = accesses.receiver(agents).expired(exclude=True)
        if isinstance(agents, Agent):
            q = Q(owner=agents) | Q(accesses__in=accesses)
        else:
            q = Q(owner__in=agents) | Q(accesses__in=accesses)
        return self.access(accesses).filter(q)

    def access(self, access: AccessQuerySet | Access, strict: bool = False) -> OwnedQuerySet:
        """Prefetch object with accesses from the provided queryset (as ``agent_accesses``).

        The items are annotated with ``access_uuid`` corresponding to the access.

        :param access: use this Access QuerySet or instance
        :param strict: if True, filter only items with prefetched access
        :return: the annotated and prefetched queryset.
        """
        if isinstance(access, self.model.Access):
            access = self.model.Access.objects.filter(pk=access.pk)

        fk_field = self.model.Access._meta.get_field("target")
        lookup = fk_field.remote_field.get_accessor_name()
        prefetch = Prefetch(lookup, access, "agent_accesses")
        access = access.filter(target=OuterRef("pk"))

        self = self.annotate(access_uuid=Subquery(access.values("uuid")[:1])).prefetch_related(prefetch)
        return self.filter(access_uuid__isnull=False) if strict else self


class Owned(models.Model, metaclass=OwnedBase):
    """An object accessible through Accesss.

    It can have a member `Access` (subclass of
    `caps.models.Access`) that is used as object's specific
    access. If none is provided, a it will be generated automatically
    for concrete classes.

    The ``Capability`` concrete model class will be set at creation, when
    the related :py:class:`Access` is created.

    This provides:

        - :py:class:`Access` concrete model accessible from the :py:class:`Owned` concrete subclass;
        - :py:class:`Capability` concrete model accessible from the :py:class:`Owned` concrete subclass;
    """

    root_grants = {}
    """
    This class attribute provide the default value for grant object.
    It should follows the structure of :py:attr:`~.access.Access.grants` field, such as:

    .. code-block:: python

        root_grants = {
            "auth.view_user": 1,
            "app.change_mymodel": 2
        }

    """

    uuid = models.UUIDField(_("Id"), default=uuid4)
    owner = models.ForeignKey(Agent, models.CASCADE, verbose_name=_("Owner"))

    objects = OwnedQuerySet.as_manager()

    detail_url_name = None
    """ Provide url name used for get_absolute_url. """

    class Meta:
        abstract = True

    @cached_property
    def access(self) -> Access:
        """Return Access to this object for receiver provided to
        OwnedQuerySet's `access()` or `accesses()`."""
        access_set = getattr(self, "agent_accesses", None)
        return access_set and access_set[0] or None

    @classmethod
    def check_root_grants(cls):
        """
        Lookup for declared permissions of :py:attr:`root_grants`, raising ValueError if
        there are declared permissions not present in database.
        """
        keys = set()
        q = Q()
        for key in cls.root_grants.keys():
            app_label, codename = key.split(".", 1)
            q |= Q(content_type__app_label=app_label, codename=codename)
            keys.add((app_label, codename))

        perms = set(Permission.objects.filter(q).values_list("content_type__app_label", "codename"))

        if delta := (keys - perms):
            raise ValueError(
                f"`{cls.__name__}.root_grants` has permissions not present in the database: {', '.join(delta)}"
            )

    def has_perm(self, user, perm: str) -> bool:
        """Return True if user has provided permission for object."""
        if self.owner.is_agent(user):
            return perm in self.root_grants
        return self.access and self.access.has_perm(user, perm) or False

    def get_all_permissions(self, user) -> set[str]:
        """Return allowed permissions for this user."""
        if self.owner.is_agent(user):
            return self.root_grants
        return self.access and self.access.get_all_permissions(user) or set()

    def share(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs) -> Access:
        """Share and save access to this object.

        See :py:meth:`get_share` for parameters.
        """
        obj = self.get_share(receiver, grants, **kwargs)
        obj.save()
        return obj

    async def ashare(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs) -> Access:
        """Share and save access to this object (async)."""
        obj = self.get_share(receiver, grants, **kwargs)
        await obj.asave()
        return obj

    def get_share(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs) -> Access:
        """Share this object to this receiver, returning new unsaved :py:class:`~.access.Access`.

        :param receiver: share's receiver
        :param grants: allowed permissions (should be in :py:attr:`root_grants`)
        :param **kwargs: extra initial arguments
        """
        if grants:
            grants = {key: min(value, grants[key]) for key, value in self.root_grants.items() if key in grants}
        else:
            grants = dict(self.root_grants.items())

        if not grants:
            raise PermissionDenied("Share not allowed.")
        return self.Access(target=self, emitter=self.owner, receiver=receiver, grants=grants, **kwargs)

    def get_absolute_url(self) -> str:
        if not self.detail_url_name:
            raise ValueError("Missing attribute `detail_url_name`.")
        if self.access:
            return self.access.get_absolute_url()
        return reverse(self.detail_url_name, kwargs={"uuid": self.uuid})
