from django.views import generic

from . import mixins

__all__ = ("OwnedListView", "OwnedDetailView", "OwnedCreateView", "OwnedUpdateView", "OwnedDeleteView")


class OwnedListView(mixins.OwnedMixin, generic.ListView):
    pass


class OwnedDetailView(mixins.SingleOwnedMixin, mixins.OwnedPermissionMixin, generic.DetailView):
    pass


class OwnedCreateView(mixins.UserAgentMixin, generic.edit.CreateView):
    pass


class OwnedUpdateView(mixins.SingleOwnedMixin, mixins.OwnedPermissionMixin, generic.edit.UpdateView):
    pass


class OwnedDeleteView(mixins.SingleOwnedMixin, mixins.OwnedPermissionMixin, generic.edit.DeleteView):
    pass
