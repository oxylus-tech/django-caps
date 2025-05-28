from __future__ import annotations
from uuid import uuid4
from typing import Iterable

from django.db import models
from django.db.models import Q, OuterRef, Prefetch, Subquery
from django.contrib.auth.models import Permission
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from .agent import Agent
from .reference import Reference, ReferenceQuerySet
from .nested import NestedModelBase

__all__ = ("ObjectBase", "ObjectQuerySet", "Object")


class ObjectBase(NestedModelBase):
    """Metaclass for Object model classes.

    It subclass Reference if no `Reference` member is provided.
    """

    nested_class = Reference

    @classmethod
    def create_nested_class(cls, new_class, name, attrs={}):
        """Provide `target` ForeignKey on nested Reference model."""
        return super(ObjectBase, cls).create_nested_class(
            new_class,
            name,
            {
                "target": models.ForeignKey(
                    new_class,
                    models.CASCADE,
                    db_index=True,
                    related_name="references",
                    verbose_name=_("Target"),
                ),
                **attrs,
            },
        )


class ObjectQuerySet(models.QuerySet):
    """QuerySet for Objects."""

    def available(self, agents: Agent | Iterable[Agent]):
        """
        Return object available to provided agents (as owner or receiver).
        :param agents: for the provided agent
        :param uuid: if provided filter for this uuid
        """
        refs = self.model.Reference.objects.receiver(agents).expired(exclude=True).select_related("receiver")
        if isinstance(agents, Agent):
            q = Q(owner=agents) | Q(references__in=refs)
        else:
            q = Q(owner__in=agents) | Q(references__in=refs)
        return self.refs(refs).filter(q)

    def refs(self, refs: ReferenceQuerySet | Reference, strict: bool = False) -> ObjectQuerySet:
        """Return Objects for the provided references.

        This method annotates the Object with ``agent_reference_set`` whose value
        is set to relevant reference(s). This allows to use :py:attr:`reference` property.

        :param refs: use this Reference QuerySet or instance
        :param strict: if True, filter only items with references
        :return: the annotated queryset.
        """
        if isinstance(refs, self.model.Reference):
            refs = self.model.Reference.objects.filter(pk=refs.pk)

        fk_field = self.model.Reference._meta.get_field("target")
        lookup = fk_field.remote_field.get_accessor_name()
        prefetch = Prefetch(lookup, refs, "agent_reference_set")
        refs = refs.filter(target=OuterRef("pk"))

        self = self.annotate(reference_id=Subquery(refs.values("id")[:1])).prefetch_related(prefetch)
        return self.filter(reference_id__isnull=False) if strict else self


class Object(models.Model, metaclass=ObjectBase):
    """An object accessible through References.

    It can have a member `Reference` (subclass of
    `caps.models.Reference`) that is used as object's specific
    reference. If none is provided, a it will be generated automatically
    for concrete classes.

    The ``Capability`` concrete model class will be set at creation, when
    the related :py:class:`Reference` is created.

    This provides:

        - :py:class:`Reference` concrete model accessible from the :py:class:`Object` concrete subclass;
        - :py:class:`Capability` concrete model accessible from the :py:class:`Object` concrete subclass;
    """

    root_grants = {}
    """
    This class attribute provide the default value for grant object.
    It should follows the structure of :py:attr:`~.reference.Reference.grants` field, such as:

    .. code-block:: python

        root_grants = {
            "auth.view_user": 1,
            "app.change_mymodel": 2
        }

    """

    uuid = models.UUIDField(_("uuid"), default=uuid4)
    owner = models.ForeignKey(Agent, models.CASCADE, verbose_name=_("Owner"))

    objects = ObjectQuerySet.as_manager()

    detail_url_name = None
    """ Provide url name used for get_absolute_url. """

    class Meta:
        abstract = True

    @cached_property
    def reference(self) -> Reference:
        """Return Reference to this object for receiver provided to
        ObjectQuerySet's `ref()` or `refs()`."""
        ref_set = getattr(self, "agent_reference_set", None)
        return ref_set and ref_set[0] or None

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
            return True
        return self.reference and self.reference.has_perm(user, perm) or False

    def get_all_permissions(self, user) -> set[str]:
        """Return allowed permissions for this user."""
        if self.owner.is_agent(user):
            return self.root_grants
        return self.reference and self.reference.get_all_permissions(user) or set()

    def share(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs) -> Reference:
        """Share and save reference to this object.

        See :py:meth:`get_shared` for parameters.
        """
        obj = self.get_shared(receiver, grants, **kwargs)
        obj.save()
        return obj

    async def ashare(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs) -> Reference:
        """Share and save reference to this object (async)."""
        obj = self.get_shared(receiver, grants, **kwargs)
        await obj.asave()
        return obj

    def get_shared(self, receiver: Agent, grants: dict[str, int] | None = None, **kwargs) -> Reference:
        """Share this object to this receiver.

        :param receiver: share's receiver
        :param grants: allowed permissions (should be in :py:attr:`root_grant`)
        :param **kwargs: extra initial arguments
        """
        if grants:
            grants = {key: min(value, grants[key]) for key, value in self.root_grants.items() if key in grants}
        else:
            grants = dict(self.root_grants.items())
        return self.Reference(target=self, emitter=self.owner, receiver=receiver, grants=grants, **kwargs)

    def get_absolute_url(self) -> str:
        if not self.detail_url_name:
            raise ValueError("Missing attribute `detail_url_name`.")
        return reverse(self.detail_url_name, kwargs={"uuid": self.uuid})
