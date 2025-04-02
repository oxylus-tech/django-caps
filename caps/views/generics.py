from django.views import generics

from . import mixins

__all__ = ("ObjectListView", "ObjectDetailView", "ObjectCreateView", "ObjectUpdateView", "ObjectDeleteView")


class ObjectListView(mixins.ObjectListMixin, generics.ListView):
    pass


class ObjectDetailView(mixins.ObjectDetailMixin, generics.DetailView):
    pass


class ObjectCreateView(mixins.ObjectCreateMixin, generics.edit.CreateView):
    def form_valid(self, form):
        ref = self.create_reference(self.agent, self.object)
        setattr(form.instance, "reference", ref)
        return super().form_valid(form)


class ObjectUpdateView(mixins.ObjectUpdateMixin, generics.edit.UpdateView):
    pass


class ObjectDeleteView(mixins.ObjectDeleteMixin, generics.edit.DeleteView):
    pass
