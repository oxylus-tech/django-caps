from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from django.db import models
from django.db.models import OuterRef, Prefetch, Subquery
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .agent import Agent
from .reference import Reference, ReferenceQuerySet
from .nested import NestedBase

__all__ = ("ObjectBase", "ObjectQuerySet", "Object")


class ObjectBase(NestedBase):
    """Metaclass for Object model classes.

    It subclass Reference if no `Reference` member is provided.
    """

    nested_class = Reference

    def __new__(mcls, name, bases, attrs):
        cls = super(ObjectBase, mcls).__new__(mcls, name, bases, attrs)
        setattr(cls, "Capability", cls.Reference.Capability)
        return cls

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
                    related_name="reference_set",
                    verbose_name=_("Target"),
                ),
                **attrs,
            },
        )


class ObjectQuerySet(models.QuerySet):
    """QuerySet for Objects."""

    def receiver(self, receiver: Agent | Iterable[Agent]) -> ObjectQuerySet:
        """Filter object for provided."""
        refs = self.models.Reference.objects.receiver(receiver)
        return self.with_refs(refs)

    def ref(
        self, receiver: Agent | Iterable[Agent] | None, uuid: UUID, refs: ReferenceQuerySet | None = None
    ) -> ObjectQuerySet:
        """Return reference for provided receiver and uuid.

        This method annotates the Object with ``agent_reference_set`` whose value
        is set to relevant reference(s). This allows to use :py:attr:`reference` property.

        Please refer to :py:meth:`ReferenceQuerySet.ref` for more information.

        :param receiver: the reference's receiver
        :param uuid: reference uuid
        :param refs: use this reference QuerySet
        """
        if refs is None:
            refs = self.model.Reference.objects
        refs = refs.refs(receiver, [uuid])
        return self.with_refs(refs).get()

    def refs(
        self,
        receiver: Agent | Iterable[Agent] | None,
        uuids: Iterable[UUID],
        refs: ReferenceQuerySet | None = None,
    ) -> ObjectQuerySet:
        """Return references for provided receiver and uuids.

        Please refer to :py:meth:`ref` and :py:meth:`ReferenceQuerySet.refs` for more information.

        :param receiver: the reference's receiver
        :param uuids: reference uuids
        :param refs: use this reference QuerySet
        """
        if refs is None:
            refs = self.model.Reference.objects
        refs = refs.refs(receiver, uuids)
        return self.with_refs(refs)

    def with_refs(self, refs_queryset: models.QuerySet) -> ObjectQuerySet:
        """Prefetch provided references. Add references prefetch for objects."""
        fk_field = self.model.Reference._meta.get_field("target")
        lookup = fk_field.remote_field.get_accessor_name()
        prefetch = Prefetch(lookup, refs_queryset, "agent_reference_set")
        refs = refs_queryset.filter(target=OuterRef("pk"))
        return (
            self.annotate(reference_id=Subquery(refs.values("id")[:1]))
            .filter(reference_id__isnull=False)
            .prefetch_related(prefetch)
        )


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

    objects = ObjectQuerySet.as_manager()

    class Meta:
        abstract = True

    @cached_property
    def reference(self):
        """Return Reference to this object for receiver provided to
        ObjectQuerySet's `ref()` or `refs()`."""
        ref_set = getattr(self, "agent_reference_set", None)
        return ref_set and ref_set[0] or None
