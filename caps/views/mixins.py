from collections.abc import Iterable


from caps.models import Agent


__all__ = (
    "ObjectMixin",
    "ObjectListMixin",
    "SingleObjectMixin",
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
    agents: Agent | list[Agent] | None = None
    """ Agents fetched using :py:meth:`get_agents`. This is set by method
    :py:meth:`get_queryset`.
    """

    def get_agents(self) -> Agent | list[Agent]:
        return self.request.agents if self.all_agents else self.request.agent

    def get_actions(self):
        return self.actions

    def get_queryset(self):
        queryset = super().get_queryset()
        if actions := self.get_actions():
            queryset = queryset.actions(actions)

        self.agents = self.get_agents()
        return queryset.receiver(self.agents)


class SingleObjectMixin(ObjectMixin):
    """Detail mixin used to retrieve Object detail.

    Note: user's reference is fetched from `get_object`, not `get_queryset`.
    """

    lookup_url_kwargs = "uuid"
    """ URL's kwargs argument used to retrieve reference uuid. """

    def get_object(self):
        uuid = self.kwargs[self.lookup_field]
        return self.get_queryset().ref(None, uuid)


class ObjectListMixin(ObjectMixin):
    actions = "list"


class ObjectDetailMixin(SingleObjectMixin):
    actions = "retrieve"


class ObjectCreateMixin(SingleObjectMixin):
    actions = "create"


class ObjectUpdateMixin(SingleObjectMixin):
    actions = "update"


class ObjectDeleteMixin(SingleObjectMixin):
    actions = "delete"
