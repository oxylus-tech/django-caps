from django.views import generics

from . import mixins

__all__ = ("ObjectListView", "ObjectDetailView", "ObjectCreateView", "ObjectUpdateView", "ObjectDeleteView")


# Note: actions are aligned to rest_framework's ones.


class ObjectListView(mixins.ObjectListMixin, generics.ListView):
    pass


class ObjectDetailView(mixins.ObjectDetailMixin, generics.DetailView):
    pass


class ObjectCreateView(mixins.ObjectCreateMixin, generics.edit.CreateView):
    pass


class ObjectUpdateView(mixins.ObjectUpdateMixin, generics.edit.UpdateView):
    pass


class ObjectDeleteView(mixins.ObjectDeleteMixin, generics.edit.DeleteView):
    pass
