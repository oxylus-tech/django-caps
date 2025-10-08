"""
This module provides Django Rest Framework permissions that run checks based on
the capability system.

Two implementations are provided: :py:class:`DjangoModelPermissions` and
:py:class:`OwnedPermissions`. The first one is the base improved class,
second is used to provide object permission checks.
"""

from collections import namedtuple

from django.http import Http404
from rest_framework import exceptions, permissions


__all__ = ("DjangoModelPermissions", "OwnedPermissions")


class DjangoModelPermissions(permissions.DjangoModelPermissions):
    """
    This base class improve base DRF's ``DjangoModelPermissions`` class.

    It provides extra features:

        - GET request also has permission check (model's ``view`` permission);
        - Maps view's ``action`` to permissions;
        - Permissions map can be provided by the view (as attribute on the view);

    When the view has ``perms_map`` attribute, it will look up there for a permission
    at first place, defaulting to self's one.

    View action will be searched before using request's method. This allows viewsets
    to specify different permissions based on the current action.
    """

    perms_map = {
        **permissions.DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
    }

    def get_required_permissions(self, view, method, model_cls) -> list[str]:
        """
        Given a view, model and HTTP method, return the list of permission codes that the user is required to have.

        Lookup for them based on viewset action if any, then on method.
        Lookup for view's ``perms_map`` before self's one if any.
        """
        kwargs = {"app_label": model_cls._meta.app_label, "model_name": model_cls._meta.model_name}

        action = getattr(view, "action", None)
        view_map = getattr(view, "perms_map", None)

        # action is selected before methods
        candidates = ((view_map, action), (self.perms_map, action), (view_map, method), (self.perms_map, method))
        for map, lookup in candidates:
            if perms_ := (map and lookup and map.get(lookup)):
                perms = perms_
                break

        if not perms:
            raise exceptions.MethodNotAllowed(method)

        return [perm % kwargs for perm in perms]

    def has_permission(self, request, view):
        if not request.user or (not request.user.is_authenticated and self.authenticated_users_only):
            return False

        if getattr(view, "_ignore_model_permissions", False):
            return True

        queryset = self._queryset(view)
        perms = self.get_required_permissions(view, request.method, queryset.model)

        return request.user.has_perms(perms)


class OwnedPermissions(permissions.DjangoObjectPermissions, DjangoModelPermissions):
    """
    This class provides object permissions check for :py:class:`~.models.owned.Owned`.

    For more information about usage, see :py:class:`DjangoModelPermissions`.
    """

    # FIXME: still in use or remove?
    Request = namedtuple("RequestInfo", ["method", "user"])
    """ Fake request providing what is required to get permissions. """

    perms_map = {
        **DjangoModelPermissions.perms_map,
        "list": ["%(app_label)s.view_%(model_name)s"],
        "retrieve": ["%(app_label)s.view_%(model_name)s"],
        "create": ["%(app_label)s.add_%(model_name)s"],
        "update": ["%(app_label)s.change_%(model_name)s"],
        "partial_update": ["%(app_label)s.change_%(model_name)s"],
        "destroy": ["%(app_label)s.delete_%(model_name)s"],
    }

    # Implementation just mock request method by providing a fake
    # request object with the viewset's action if required.

    def has_object_permission(self, request, view, obj):
        # authentication checks have already been executed via has_permission
        queryset = self._queryset(view)
        model_cls = queryset.model
        user = request.user

        perms = self.get_required_permissions(view, request.method, model_cls)

        if not user.has_perms(perms, obj):
            if request.method in permissions.SAFE_METHODS:
                raise Http404

            read_perms = self.get_required_permissions(view, "GET", model_cls)
            if read_perms and not user.has_perms(read_perms, obj):
                raise Http404
            return False
        return True
