from caps.models import Agent


__all__ = (
    "BaseObjectMixin",
    "ObjectListMixin",
    "ObjectDetailMixin",
)


class BaseObjectMixin:
    """Mixin providing functionalities to work with Object model."""

    all_agents: bool = False
    """
    When this parameter is ``True``, it filter object's reference using
    all user's assigned agents instead of only the current one.
    """

    def get_agents(self) -> Agent | list[Agent]:
        return self.request.agents if self.all_agents else self.request.agent


class ObjectListMixin(BaseObjectMixin):
    """List mixin used to retrieve Object list."""

    def get_queryset(self):
        agents = self.get_agents()
        return super().get_queryset().receiver(agents)


class ObjectDetailMixin(BaseObjectMixin):
    """Detail mixin used to retrieve Object detail.

    Note: user's reference is fetched from `get_object`, not `get_queryset`.
    """

    lookup_field = "uuid"

    def get_object(self):
        agents = self.get_agents()
        uuid = self.kwargs[self.lookup_field]
        return self.get_queryset().ref(agents, uuid)
