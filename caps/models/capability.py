from __future__ import annotations
import inspect
from collections.abc import Iterable
import operator
from typing import TypeAlias

from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as __
from django.utils.translation import gettext_lazy as _

__all__ = ("CapabilityQuerySet", "Capability")


CanOne: TypeAlias = Permission | int | tuple[str, int | ContentType | type]
"""
Describe lookup for a capability's permission.

It either can be:

    - A Permission or a permission id;
    - A tuple with Permission codename, and content type (id, \
      ContentType instance, or model class);
    - An action, that will be constructed with provided model, such as:
      ``permission_codename = f"{action}_{model_name}"``.

It is used by :py:meth:`CapabilityQuerySet.can`
"""
CanMany: TypeAlias = CanOne | Iterable[CanOne]
"""
Describe lookup value for multiple capabilities' description.

It is used by :py:meth:`CapabilityQuerySet.can`
"""


class CapabilityQuerySet(models.QuerySet):
    """Queryset and manager used by Capability models."""

    def can(self, *args, **kwargs) -> CapabilityQuerySet:
        """Filter using provided permission(s).

        For parameters, look up to :py:meth:`can_many_lookup`.
        """
        return self.filter(self.can_q(*args, **kwargs))

    @classmethod
    def can_all_q(cls, *args, **kwargs):
        """Shortcut to :py:meth:`can_many_lookup` with ``&`` operator."""
        return cls.can_q(*args, op=operator.and_, **kwargs)

    @classmethod
    def can_q(
        cls, permissions: CanMany | None, prefix: str = "permission__", model: type | None = None, op=operator.or_
    ):
        """
        Return Q lookup for multiple permissions, joined using the provided operator.

        It uses result of :py:meth:`can_one_lookup`.

        :param permissions: the permissions to look for.
        :param prefix: passed down to :py:meth:`can_one_lookup`.
        :param model: passed down to :py:meth:`can_one_lookup`.
        :param op: operator to use (default to `|`)
        """
        if isinstance(permissions, (Permission, int, tuple)):
            return Q(**cls.can_one_lookup(permissions))

        q = Q()
        if permissions:
            for perm in permissions:
                q_ = Q(**cls.can_one_lookup(perm, "capability__permission__"))
                q = op(q, q_)
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
            ct = ContentType.objects.get_for_model(model)
            return {
                f"{prefix}codename": f"{permission}_{model._meta.model_name}",
                f"{prefix}content_type": ct,
            }
        elif not isinstance(permission, tuple):
            raise ValueError(f"Invalid type for permission: `{type(permission)}`")

        codename, ct = permission
        kwargs = {f"{prefix}codename": codename}
        if isinstance(ct, ContentType):
            kwargs[f"{prefix}content_type"] = ct
        elif inspect.isclass(ct) and issubclass(ct, models.Model):
            kwargs[f"{prefix}content_type"] = ContentType.objects.get_for_model(ct)
        elif isinstance(ct, int):
            kwargs[f"{prefix}content_type_id"] = ct
        else:
            raise ValueError(f"Invalid type for permission's content type: `{ct}`")
        return kwargs

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
    """

    permission = models.ForeignKey(Permission, models.CASCADE)
    """ Related permission """
    max_derive = models.PositiveIntegerField(_("Maximum Derivation"), default=0)
    """ Maximum allowed derivations. """

    objects = CapabilityQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = (("reference", "permission_id"),)

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
        :return the new unsaved Capability.

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
