from django.views import generic

from . import mixins

__all__ = ("ObjectListView", "ObjectDetailView", "ObjectCreateView", "ObjectUpdateView", "ObjectDeleteView")


class ObjectListView(mixins.ObjectMixin, generic.ListView):
    pass


class ObjectDetailView(mixins.SingleObjectMixin, mixins.ObjectPermissionMixin, generic.DetailView):
    pass


class ObjectCreateView(generic.edit.CreateView):
    pass


class ObjectUpdateView(mixins.SingleObjectMixin, mixins.ObjectPermissionMixin, generic.edit.UpdateView):
    pass


class ObjectDeleteView(mixins.SingleObjectMixin, mixins.ObjectPermissionMixin, generic.edit.DeleteView):
    pass
