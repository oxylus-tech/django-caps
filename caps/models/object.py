from __future__ import annotations


from django.db import models
from django.db.models import Q, OuterRef, Prefetch, Subquery
from django.contrib.auth.models import Permission
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

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

    def refs(
        self,
        refs: ReferenceQuerySet | Reference,
    ) -> ObjectQuerySet:
        """Return Objects for the provided references.

        This method annotates the Object with ``agent_reference_set`` whose value
        is set to relevant reference(s). This allows to use :py:attr:`reference` property.

        :param refs: use this Reference QuerySet or instance
        :return: the annotated queryset.
        """
        if isinstance(refs, self.model.Reference):
            refs = self.model.Reference.objects.filter(pk=refs.pk)

        fk_field = self.model.Reference._meta.get_field("target")
        lookup = fk_field.remote_field.get_accessor_name()
        prefetch = Prefetch(lookup, refs, "agent_reference_set")
        refs = refs.filter(target=OuterRef("pk"))

        # FIXME: add filter reference__in=refs ?
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

    root_reference_grants = {}
    """
    This class attribute provide the default value for grant object.
    It should follows the structure of :py:attr:`~.reference.Reference.grants` field, such as:

    .. code-block:: python

        root_reference_grants = {
            "auth.view_user": 1,
            "app.change_mymodel": 2
        }

    """

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
    def check_root_reference_grants(cls):
        """
        Lookup for declared permissions of :py:attr:`root_reference_grants`, raising ValueError if
        there are declared permissions not present in database.
        """
        keys = set()
        q = Q()
        for key in cls.root_reference_grants.keys():
            app_label, codename = key.split(".", 1)
            q |= Q(content_type__app_label=app_label, codename=codename)
            keys.add((app_label, codename))

        perms = set(Permission.objects.filter(q).values_list("content_type__app_label", "codename"))

        if delta := (keys - perms):
            raise ValueError(
                f"`{cls.__name__}.root_reference_grants` has permissions not present in the database: {', '.join(delta)}"
            )

    def get_absolute_url(self) -> str:
        """
        Return absolute url to object based on :py:attr:`reference`.
        It uses :py:attr:`detail_url_name` to do so.

        This means that the object must have been fetched from db using
        :py:meth:`ObjectQuerySet.refs`.

        This method is a shortcut to related :py:class:`Reference.get_absolute_url`.

        :yield ValueError: when :py:attr:`reference` or :py:attr:`detail_url_name` is missing.
        """
        if not self.reference:
            raise ValueError("The Object instance MUST be fetched using `ObjectQuerySet.refs`")
        return self.reference.get_absolute_url()
