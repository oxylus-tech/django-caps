from django.views import generic
from django.http import HttpResponseRedirect

from . import mixins

__all__ = ("ObjectListView", "ObjectDetailView", "ObjectCreateView", "ObjectUpdateView", "ObjectDeleteView")


class ObjectListView(mixins.ObjectMixin, generic.ListView):
    pass


class ObjectDetailView(mixins.ObjectPermissionMixin, generic.DetailView):
    pass


class ObjectCreateView(mixins.ObjectCreateMixin, generic.edit.CreateView):
    def form_valid(self, form):
        # we have to reimplement this method because create_root must
        # be called before returning the success_url.
        self.object = form.save()
        self.create_reference(self.agent, self.object)
        return HttpResponseRedirect(self.get_success_url())


class ObjectUpdateView(mixins.ObjectPermissionMixin, generic.edit.UpdateView):
    pass


class ObjectDeleteView(mixins.ObjectPermissionMixin, generic.edit.DeleteView):
    pass
