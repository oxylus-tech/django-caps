from django.views import generic
from django.http import HttpResponseRedirect

from . import mixins

__all__ = ("ObjectListView", "ObjectDetailView", "ObjectCreateView", "ObjectUpdateView", "ObjectDeleteView")


class ObjectListView(mixins.ObjectListMixin, generic.ListView):
    pass


class ObjectDetailView(mixins.ObjectDetailMixin, generic.DetailView):
    pass


class ObjectCreateView(mixins.ObjectCreateMixin, generic.edit.CreateView):
    def form_valid(self, form):
        # we have to reimplement this method because create_root must
        # be called before returning the success_url.
        self.object = form.save()
        ref = self.create_reference(self.agent, self.object)
        setattr(self.object, "reference", ref)
        return HttpResponseRedirect(self.get_success_url())


class ObjectUpdateView(mixins.ObjectUpdateMixin, generic.edit.UpdateView):
    pass


class ObjectDeleteView(mixins.ObjectDeleteMixin, generic.edit.DeleteView):
    pass
