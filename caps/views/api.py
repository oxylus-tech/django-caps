from django.db.models import Q
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


class ObjectRetrieveAPIView(mixins.ObjectDetailMixin, generics.RetrieveAPIView):
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
        "list": ObjectListAPIView.can,
        "retrieve": ObjectRetrieveAPIView.can,
        "create": ObjectCreateAPIView.can,
        "update": ObjectUpdateAPIView.can,
        "destroy": ObjectDestroyAPIView.can,
    }
    """ Map of ViewSet actions to references' ones. """

    def get_can_all_q(self) -> list[Q]:
        """ Return Q object for filtering reference on :py:attr:`can` attribute and current request action. """
        cls = self.get_reference_class()
        can = self.can and self.can.get(self.action)
        return self._get_can_all_q(cls, can) if can else []


class ObjectViewSet(ViewSetMixin, viewsets.ModelViewSet):
    pass
