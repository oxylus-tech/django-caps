"""Provide Django Rest Framework permissions to work with capabilities."""

from rest_framework.permissions import BasePermission

from caps.models import Capability, Object

__all__ = (
    "IsAllowed",
    "IsActionAllowed",
)


class IsAllowed(BasePermission):
    """Return ``True`` if capability is allowed."""

    capability_name = None

    def __init__(self, capability_name=None):
        if capability_name:
            self.capability_name = capability_name

    def has_object_permission(self, request, view, obj):
        return isinstance(obj, Object) and bool(obj.reference.get_capability(self.capability_name))


class IsActionAllowed(BasePermission):
    """Permission allowed for a specific action and object. It uses
    :py:meth:`caps.model.Capability.get_name` to get name from object's model and view action.

    Objects must be instances of :py:class`caps.models.Object`. Retrieve action name
    from ``view.action`` (defaults to self's ``action``).
    """

    def __init__(self, action=None):
        self.action = action

    def has_object_permission(self, request, view, obj):
        action = getattr(view, "action", self.action)
        if not isinstance(obj, Object) or action is None:
            return False

        model = type(obj)
        capability_name = Capability.get_name(model, action)
        return bool(obj.reference.get_capability(capability_name))
