from .models import Agent, Object, Reference
from .models.capability import CanMany


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

    agent: Agent | None = None
    """ Current request's agent. """
    agents: Agent | list[Agent] | None = None
    """ Agents fetched using :py:meth:`get_agents`. This is set by method
    :py:meth:`get_queryset`.
    """

    def get_agents(self) -> Agent | list[Agent]:
        return self.request.agents if self.all_agents else self.request.agent

    def get_queryset(self):
        return super().get_queryset().receiver(self.agents)

    def dispatch(self, request, *args, **kwargs):
        self.agents = self.get_agents()
        self.agent = request.agent
        return super().dispatch(request, *args, **kwargs)


class ObjectPermissionMixin:
    can: CanMany
    """ Capability permission(s) required to display the view.

    A string with Permission codename. ContentType will be matched \
    against current Capability's target :py:class:`.object.Object`.
    """

    def get_reference_queryset(self):
        """Return queryset for references."""
        if not hasattr(self, "_reference_queryset"):
            # we cache reference queryset for permission lookup
            query = self.model.Reference.objects
            if self.can:
                query = query.can_all(self.can)
            else:
                query = query.all()
            setattr(self, "_reference_queryset", query)
        return self._reference_queryset

    def get_queryset(self):
        return super().get_queryset().refs(self.get_reference_queryset())


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
    reference_class = None
    """ Reference class (defaults to model's Reference). """

    actions = "create"

    def get_reference_class(self):
        """Return reference class used to create reference for object."""
        cls = self.reference_class or getattr(self.model, "Reference", None)
        if cls is None:
            raise ValueError("There is no Reference class provided for this model nor this view.")
        if not issubclass(cls, Reference):
            raise ValueError("{cls} is not a Reference subclass.")
        return cls

    def create_reference(self, emitter: Agent, target: Object):
        cls = self.get_reference_class()
        ref = cls.objects.create_root(emitter, target)
        setattr(object, "reference", ref)
        return ref


class ObjectUpdateMixin(SingleObjectMixin):
    actions = "update"


class ObjectDeleteMixin(SingleObjectMixin):
    actions = "delete"
