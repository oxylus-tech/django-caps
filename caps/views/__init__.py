from .generics import ObjectListView, ObjectDetailView, ObjectCreateView, ObjectUpdateView, ObjectDeleteView
from .api import (
    ObjectListAPIView,
    ObjectRetrieveAPIView,
    ObjectCreateAPIView,
    ObjectUpdateAPIView,
    ObjectDestroyAPIView,
    ObjectViewSet,
)
from .common import (
    AgentDetailView,
    AgentListView,
    AgentCreateView,
    AgentUpdateView,
    AgentDeleteView,
    ReferenceDetailView,
    ReferenceListView,
    ReferenceDeleteView,
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
    "ObjectViewSet",
    "AgentDetailView",
    "AgentListView",
    "AgentCreateView",
    "AgentUpdateView",
    "AgentDeleteView",
    "ReferenceDetailView",
    "ReferenceListView",
    "ReferenceDeleteView",
)
