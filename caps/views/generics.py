from django.views import generics

from . import mixins

__all__ = ("ObjectListView", "ObjectDetailView", "ObjectCreateView", "ObjectUpdateView", "ObjectDeleteView")


class ObjectListView(mixins.ObjectListMixin, generics.ListView):
    pass


class ObjectDetailView(mixins.ObjectDetailMixin, generics.DetailView):
    pass


class ObjectCreateView(mixins.ObjectCreateMixin, generics.edit.CreateView):
    pass
    # def form_valid(self, form):
    # self.object = form.save()
    # _reference = self.create_reference(self.agent, self.object)
    # return get_success_url


class ObjectUpdateView(mixins.ObjectUpdateMixin, generics.edit.UpdateView):
    pass


class ObjectDeleteView(mixins.ObjectDeleteMixin, generics.edit.DeleteView):
    pass
