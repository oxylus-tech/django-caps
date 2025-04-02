from .models import Agent, Object, Reference
from .models.capability import CanMany


__all__ = (
    "ObjectMixin",
    "ObjectPermissionMixin",
    "SingleObjectMixin",
    "ObjectListMixin",
    "ObjectDetailMixin",
    "ObjectCreateMixin",
    "ObjectUpdateMixin",
    "ObjectDeleteMixin",
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

    reference_class = None
    """ Reference class (defaults to model's Reference). """

    def get_agents(self) -> Agent | list[Agent]:
        return self.request.agents if self.all_agents else self.request.agent

    def get_reference_queryset(self):
        """Return reference queryset used to select objects."""
        return self.get_reference_class().object.receiver(self.agents)

    @classmethod
    def get_reference_class(cls):
        """Return reference class used to create reference for object."""
        if not cls.reference_class:
            try:
                cls.reference_class = getattr(cls.model, "Reference")
            except AttributeError:
                raise ValueError("There is no Reference class provided for this model nor this view.")
        if not issubclass(cls.reference_class, Reference):
            raise ValueError("{cls_} is not a Reference subclass.")
        return cls.reference_class

    def get_queryset(self):
        """Get Object queryset based get_reference_queryset."""
        refs = self.get_reference_queryset()
        return super().get_queryset().refs(refs)

    def dispatch(self, request, *args, **kwargs):
        self.agents = self.get_agents()
        self.agent = request.agent
        return super().dispatch(request, *args, **kwargs)


class ObjectPermissionMixin(ObjectMixin):
    can: CanMany
    """ Capability permission(s) required to display the view.

    A string with Permission codename. ContentType will be matched \
    against current Capability's target :py:class:`.object.Object`.
    """

    @classmethod
    def get_can_all_q(cls, can: CanMany | None = None):
        """Retun Permission q object.

        This is a class method because it is meaned to optimize reference lookup by caching at class level
        in :py:meth:`get_reference_queryset`.
        """
        can = can or cls.can
        return cls.get_reference_class().objects.can_all_q(can)

    def get_reference_queryset(self):
        """Return queryset for references."""
        cls = type(self)
        if not hasattr(cls, "_permissions_q"):
            setattr(cls, "_permissions_q", cls.get_can_all_q())
        return super().get_reference_queryset().filter(cls._permissions_q)


class SingleObjectMixin(ObjectPermissionMixin):
    """Detail mixin used to retrieve Object detail.

    Note: user's reference is fetched from `get_object`, not `get_queryset`.
    """

    lookup_url_kwargs = "uuid"
    """ URL's kwargs argument used to retrieve reference uuid. """

    def get_reference_queryset(self):
        uuid = self.kwargs[self.lookup_url_kwargs]
        return self.get_reference_queryset().filter(uuid=uuid)

    def get_object(self):
        return self.get_queryset().get()


class ObjectListMixin(ObjectPermissionMixin):
    can = "view"


class ObjectDetailMixin(SingleObjectMixin):
    can = "view"


class ObjectCreateMixin(SingleObjectMixin):
    can = "add"

    def create_reference(self, emitter: Agent, target: Object):
        cls = self.get_reference_class()
        ref = cls.objects.create_root(emitter, target)
        setattr(object, "reference", ref)
        return ref


class ObjectUpdateMixin(SingleObjectMixin):
    can = "change"


class ObjectDeleteMixin(SingleObjectMixin):
    can = "delete"
