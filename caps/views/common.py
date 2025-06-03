from django.views import generic

from . import mixins


__all__ = (
    "AgentDetailView",
    "AgentListView",
    "AgentCreateView",
    "AgentUpdateView",
    "AgentDeleteView",
    "AccessDetailView",
    "AccessListView",
    "AccessDeleteView",
)


class AgentDetailView(mixins.AgentMixin, generic.DetailView):
    permission_required = "caps.view_agent"


class AgentListView(mixins.AgentMixin, generic.ListView):
    permission_required = "caps.view_agent"


class AgentCreateView(mixins.AgentMixin, generic.CreateView):
    """Create an Agent (only for group)."""

    permission_required = "caps.add_agent"
    fields = ["group"]


class AgentUpdateView(mixins.AgentMixin, generic.edit.UpdateView):
    permission_required = "caps.add_agent"
    fields = ["group"]


class AgentDeleteView(mixins.AgentMixin, generic.edit.DeleteView):
    permission_required = "caps.delete_agent"


class AccessDetailView(mixins.AccessMixin, generic.DetailView):
    def get_queryset(self):
        """Ensure capabilities are paccessetch at the same time than the access."""
        return super().get_queryset().prefetch_related("capabilities")


class AccessListView(mixins.AccessMixin, generic.ListView):
    pass


class AccessDeleteView(mixins.AccessMixin, generic.DeleteView):
    pass
