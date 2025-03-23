from collections.abc import Iterable

from caps.models import Agent


__all__ = (
    "ObjectMixin",
    "ObjectListMixin",
    "ObjectDetailMixin",
)


class ObjectMixin:
    """Mixin providing functionalities to work with Object model."""

    all_agents: bool = False
    """
    When this parameter is ``True``, it filter object's reference using
    all user's assigned agents instead of only the current one.
    """

    actions: str | Iterable[str] | None = None
    """ Required action(s) in order to run the view. """

    def get_agents(self) -> Agent | list[Agent]:
        return self.request.agents if self.all_agents else self.request.agent

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.actions:
            return queryset.actions(self.actions)
        return queryset


class ObjectListMixin(ObjectMixin):
    """List mixin used to retrieve Object list."""

    def get_queryset(self):
        agents = self.get_agents()
        return super().get_queryset().receiver(agents)


class ObjectDetailMixin(ObjectMixin):
    """Detail mixin used to retrieve Object detail.

    Note: user's reference is fetched from `get_object`, not `get_queryset`.
    """

    lookup_field = "ref"

    def get_object(self):
        agents = self.get_agents()
        ref = self.kwargs[self.lookup_field]
        queryset = self.get_queryset()
        return queryset.ref(agents, ref)
