from .generics import ObjectListView, ObjectDetailView, ObjectCreateView, ObjectUpdateView, ObjectDeleteView
from .api import (
    ObjectListAPIView,
    ObjectRetrieveAPIView,
    ObjectCreateAPIView,
    ObjectUpdateAPIView,
    ObjectDestroyAPIView,
    ViewSetMixin,
    ObjectViewSet,
)


__all__ = (
    "ObjectListView",
    "ObjectDetailView",
    "ObjectCreateView",
    "ObjectUpdateView",
    "ObjectDeleteView",
    "ObjectListAPIView",
    "ObjectRetrieveAPIView",
    "ObjectCreateAPIView",
    "ObjectUpdateAPIView",
    "ObjectDestroyAPIView",
    "ViewSetMixin",
    "ObjectViewSet",
    #    "ModelViewSet",
    #    "GenericViewSet",
)
