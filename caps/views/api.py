from rest_framework import generics, viewsets

from ..models.capability import CanMany
from . import mixins


__all__ = (
    "ObjectListAPIView",
    "ObjectRetrieveAPIView",
    "ObjectCreateAPIView",
    "ObjectUpdateAPIView",
    "ObjectDestroyAPIView",
    "ViewSetMixin",
    "ObjectViewSet",
)


class ObjectListAPIView(mixins.ObjectListMixin, generics.ListAPIView):
    pass


class ObjectRetrieveAPIView(mixins.ObjectDetailMixin, generics.DetailAPIView):
    pass


class ObjectCreateAPIView(mixins.ObjectCreateMixin, generics.CreateAPIView):
    pass


class ObjectUpdateAPIView(mixins.ObjectUpdateMixin, generics.UpdateAPIView):
    pass


class ObjectDestroyAPIView(mixins.ObjectDeleteMixin, generics.DestroyAPIView):
    pass


class ViewSetMixin(mixins.SingleObjectMixin):
    """
    This is the base mixin handling permission check for django-caps.

    It provides mapping between actions and specific permissions.

    """

    can: dict[str, CanMany] = {
        "list": ObjectListAPIView.actions,
        "retrieve": ObjectRetrieveAPIView.actions,
        "create": ObjectCreateAPIView.actions,
        "update": ObjectUpdateAPIView.actions,
        "destroy": ObjectDestroyAPIView.actions,
    }
    """ Map of ViewSet actions to references' ones. """

    def get_action(self):
        return self.actions.get(self.action)

    @classmethod
    def get_can_all_q(cls, can: CanMany | None):
        can = can or {}
        defaults = {key: super(ViewSetMixin, cls).get_can_all_q(perms) for key, perms in cls.can.items()}
        return {**defaults, **can}


class ObjectViewSet(ViewSetMixin, viewsets.ModelViewSet):
    pass
