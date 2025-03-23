from django.views import generics

from .mixins import ObjectDetailMixin, ObjectListMixin

__all__ = ("ObjectListView", "ObjectDetailView", "ObjectChangeView", "ObjectDeleteView")


class ObjectListView(ObjectListMixin, generics.ListView):
    actions = "view"


class ObjectDetailView(ObjectDetailMixin, generics.DetailView):
    actions = "view"


class ObjectChangeView(ObjectDetailMixin, generics.edit.UpdateView):
    actions = "change"


class ObjectDeleteView(ObjectDetailMixin, generics.edit.DeleteView):
    actions = "delete"
