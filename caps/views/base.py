from django.views import generics

from .mixins import ObjectDetailMixin, ObjectListMixin

__all__ = ("ObjectListView", "ObjectDetailView")


class ObjectListView(ObjectListMixin, generics.ListView):
    action = "list"


class ObjectDetailView(ObjectDetailMixin, generics.DetailView):
    action = "retrieve"
