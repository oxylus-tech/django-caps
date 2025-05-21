from collections import namedtuple

from rest_framework import permissions, viewsets


__all__ = ("DjangoModelPermissions", "ObjectPermissions")


class DjangoModelPermissions(permissions.DjangoModelPermissions):
    """Subclass DRF DjangoModelPermissions in order to add "view" permission on GET request."""

    perms_map = {
        **permissions.DjangoModelPermissions.perms_map,
        "GET": ["%(app_label)s.view_%(model_name)s"],
    }


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

    def has_permission(self, request, view):
        return super().has_permission(self._get_request(request, view), view)

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(self._get_request(request, view), view, obj)

    def _get_request(self, request, view):
        if isinstance(view, viewsets.ViewSet) and view.action in self.perms_map:
            return self.Request(view.action, request.user)
        return request
