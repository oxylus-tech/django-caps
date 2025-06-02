from collections import namedtuple

from django.http import Http404
from rest_framework import exceptions, permissions


__all__ = ("DjangoModelPermissions", "ObjectPermissions")


class DjangoModelPermissions(permissions.DjangoModelPermissions):
    """
    Provide DjangoModelPermissions with "view" permission for GET request.

    It also supports providing ``perms_map`` on the view: permissions will be looked up in view' perms_map if
    present before looking up on self. If ``view.action`` is provided,

    View action will be searched before using request's method.

    This is an adapted version of Django Rest Framework's class.
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
        perms = view_map and self._get_permissions(view_map, action, method)
        if not perms:
            perms = self._get_permissions(self.perms_map, action, method)

        if not perms:
            raise exceptions.MethodNotAllowed(method)

        return [perm % kwargs for perm in perms]

    def _get_permissions(self, perms_map, action, method) -> None | list[str]:
        """Using provided permission map, action and method return permissions if any."""
        if perms := (action and perms_map.get(action)):
            return perms
        if perms := perms_map.get(method):
            return perms

    def has_permission(self, request, view):
        if not request.user or (not request.user.is_authenticated and self.authenticated_users_only):
            return False

        if getattr(view, "_ignore_model_permissions", False):
            return True

        queryset = self._queryset(view)
        perms = self.get_required_permissions(view, request.method, queryset.model)

        return request.user.has_perms(perms)


class ObjectPermissions(permissions.DjangoObjectPermissions, DjangoModelPermissions):
    """
    This class provide permissions check over object using a permission map.

    The mapped permissions can either a request method or a viewset action (in case this is used with viewsets).
    """

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
        # authentication checks have already executed via has_permission
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
