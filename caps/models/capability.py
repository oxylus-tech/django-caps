from __future__ import annotations
import inspect
from collections.abc import Iterable
from typing import TypeAlias

from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as __
from django.utils.translation import gettext_lazy as _

__all__ = ("CapabilityQuerySet", "Capability")


CanOne: TypeAlias = Permission | str | int | tuple[str, ContentType | type]
"""
Describe lookup for a capability's permission. It is used by :py:meth:`CapabilityQuerySet.can` and all related methods (:py:meth:`CapabilityQuerySet.can_one_lookup`, :py:meth:`CapabilityQuerySet.can_q`, etc.)

It either can be:

    - A Permission or a permission id;
    - A tuple with Permission action, and content type (ContentType instance, or model class);
    - A single action combined with provided `model` argument.

An action is the part of the Django's ``Permission.codename`` specifying a verb. Based on the provided model
(or content type), the codename will be constructed as: ``permission_codename = f"{action}_{model_name}"``.

"""
CanMany: TypeAlias = CanOne | Iterable[CanOne]
"""
Describe lookup value for multiple capabilities' description.

It is used by :py:meth:`CapabilityQuerySet.can`
"""


class CapabilityQuerySet(models.QuerySet):
    """
    Queryset and manager used by Capability models.

    It provide `can` filter method + other utilities methods
    in order to build up filter's lookups (used by :py:class:`~.reference.Reference`).
    """

    def can(self, permissions: CanMany | None) -> CapabilityQuerySet:
        """Filter using provided permission(s).

        Permissions provided as action string are matched with capability's concrete :py:class:`~.object.Object` model:

        .. code-block::

            # We assume: app.MyObject <- Reference <- Capability

            # Look up for `app.view_myobject`.
            query = Capability.objects.can("view")

            # Look up for capabilities with an OR joint on permissions.
            permission = Permission.objects.all().first()
            query = Capability.objects.can((
                'view',
                # with an instance of permission
                permission,
                # with an action and some other model
                ('change', SomeModel),
            ))

        :param permissions: the permissions to look for.
        :yield: from :py:meth:`can_one_lookup`.
        """
        return self.filter(self.can_q(permissions, model=self.model.get_object_class()))

    @classmethod
    def can_all_q(cls, permissions: CanMany, prefix: str = "permission__", model: type | None = None) -> list[Q]:
        """
        Return a list of Q objects for each provided permissions, using : py:meth:`can_one_lookup`.

        :param permissions: the permissions to look for.
        :param prefix: passed down to :py:meth:`can_one_lookup`.
        :param model: passed down to :py:meth:`can_one_lookup`.
        """
        if isinstance(permissions, (Permission, str, int, tuple)):
            return [Q(**cls.can_one_lookup(permissions, prefix, model))]

        return [Q(**cls.can_one_lookup(perm, prefix, model)) for perm in permissions]

    @classmethod
    def can_q(cls, permissions: CanMany, prefix: str = "permission__", model: type | None = None) -> Q:
        """
        Return Q lookup for multiple permissions joined with `|`, using  :py:meth:`can_one_lookup`.

        :param permissions: the permissions to look for.
        :param prefix: passed down to :py:meth:`can_one_lookup`.
        :param model: passed down to :py:meth:`can_one_lookup`.
        """
        if isinstance(permissions, (Permission, str, int, tuple)):
            return Q(**cls.can_one_lookup(permissions, prefix, model))

        q = Q()
        for perm in permissions:
            q |= Q(**cls.can_one_lookup(perm, prefix, model))
        return q

    @staticmethod
    def can_one_lookup(
        permission: CanOne, prefix: str = "permission__", model: type | None = None
    ) -> dict[str, str | int]:
        """Return lookup for one permission.

        :param permission: to get lookup for.
        :param prefix: prefix keys with this value.
        :param model: model class to use when only action is provided.
        :return lookup argument dictionnary.

        :yield ValueError: on unsupported ``permission`` types.

        """
        if isinstance(permission, Permission):
            return {f"{prefix}id": permission.id}
        elif isinstance(permission, int):
            return {f"{prefix}id": permission}
        elif isinstance(permission, str):
            if model is None:
                raise ValueError("You must provide a `model` when specifying a permission codename.")
            action, ct = permission, ContentType.objects.get_for_model(model)
        elif isinstance(permission, (tuple, list)):
            action, ct = permission
            if inspect.isclass(ct) and issubclass(ct, models.Model):
                ct = ContentType.objects.get_for_model(ct)
            elif not isinstance(ct, ContentType):
                raise ValueError(f"Invalid type for permission (`{ct}`): it must be a ContentType or model class")
        else:
            raise ValueError(f"Invalid type for permission: `{type(permission)}`")

        return {f"{prefix}codename": f"{action}_{ct.model}", f"{prefix}content_type": ct}

    def initials(self):
        """Filter capabilities used as initial values of a Reference."""
        return self.filter(reference__isnull=True)


class Capability(models.Model):
    """A single capability providing permission for executing a single action.

    It is linked to an object by a :py:class:`~.reference.Reference`. The reference
    is the entry point for user to address/access the object. The capability represent
    what he can do.

    This model is provided as abstract model whose implementation MUST provide
    a ``reference`` foreign key to a :py:class:`~.reference.Reference` (reverse
    relation: `capabilities`). The foreign key is nullable, ``None`` have special
    meaning: it represents default assigned capabilities to newly created root Reference instances. They can be fetched using :py:meth:`CapabilityQuerySet.get_initials`.

    See :py:class:`~.reference.Reference` documentation for more information.

    It is recommanded to ``select_related`` permission in order to read
    :py:attr:`name` and :py:attr:`codename`.

    Derivation
    ----------

    Capability can derived: it means the permission is shared to another agent.
    To be allowed to share, :py:attr:`max_derive` must be greater than 0. When sharing
    only a lower value is allowed to the new capability's field.

    Lets see what it does:

    .. code-block:: python

        from models import MyObject

        permission = Permission.objects.all().first()
        cap = MyObject.Capability(permission=permission, max_derive=2)
        #  `cap` is not saved, we don't core to provide a reference for this example.

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

    **Note:** You'll more work over references for derivation than capabilities themselves.
    """

    permission = models.ForeignKey(Permission, models.CASCADE, related_name="capabilities")
    """ Related permission """
    max_derive = models.PositiveIntegerField(_("Maximum Derivation"), default=0)
    """ Maximum allowed derivations. """

    objects = CapabilityQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = (("reference", "permission_id"),)
        verbose_name = _("Capability")
        verbose_name_plural = _("Capabilities")

    @classmethod
    def get_reference_class(cls):
        """Return related Reference class."""
        return cls.reference.field.related_model

    @classmethod
    def get_object_class(cls):
        """Return related Object class."""
        return cls.get_reference_class().target.field.related_model

    def can_derive(self, max_derive: None | int = None) -> bool:
        """Return True if this capability can be derived."""
        return self.max_derive > 0 and (max_derive is None or max_derive < self.max_derive)

    def derive(self, max_derive: None | int = None, reference=None, **kwargs) -> Capability:
        """Derive a new capability from self (without checking existence in
        database).

        :param max_derive: when value is None, it will based the value on self's \
                py:attr:`max_derive` minus 1.
        :param **kwargs: extra initial argument of the new Capability
        :return: the new unsaved Capability.

        :yield PermissionDenied: when Capability derivation is not allowed.
        """
        # disallowed values as they are provided by self.
        if "permission" in kwargs or "permission_id" in kwargs:
            raise ValueError("Providing `permission_id` or `permission` is forbidden.")

        if reference:
            if reference.target != self.reference.target:
                raise ValueError("New capability's reference must target the same object as current one's.")
            kwargs["reference"] = reference

        if not self.can_derive(max_derive):
            raise PermissionDenied(__("Can not derive capability {}").format(self))
        if max_derive is None:
            max_derive = self.max_derive - 1

        if "permission" in self.__dict__:
            kwargs["permission"] = self.permission
        else:
            kwargs["permission_id"] = self.permission_id

        return type(self)(max_derive=max_derive, **kwargs)

    def is_derived(self, capability: Capability = None) -> bool:
        """Return True if `capability` is derived from this one."""
        return self.permission_id == capability.permission_id and self.can_derive(capability.max_derive)

    def __str__(self):
        return f"{type(self).__name__}(pk={self.pk}, permission={self.permission_id}, max_derive={self.max_derive})"

    def __contains__(self, other: Capability):
        """Return True if other `capability` is derived from `self`."""
        return self.is_derived(other)

    def __eq__(self, other: Capability):
        if not isinstance(other, Capability):
            return False
        if self.pk and other.pk:
            return self.pk == other.pk
        return self.permission_id == other.permission_id and self.max_derive == other.max_derive
