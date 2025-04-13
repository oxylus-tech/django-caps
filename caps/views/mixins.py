import inspect
from functools import cache

from django.db.models import Q
from django.shortcuts import get_object_or_404

from ..models import Agent, Object, Reference
from ..models.capability import CanMany


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
    """
    Base mixin providing functionalities to work with :py:class:`~caps.models.object.Object` model.

    It provides:

        - assign self's :py:attr:`agent` and :py:attr:`agents`
        - queryset to available :py:class:`~caps.models.reference.Reference`.

    """

    all_agents: bool = False
    """
    When this parameter is ``True``, it filter object's reference using
    all user's assigned agents instead of only the current one. See :py:attr:`agents` for more information.
    """

    agent: Agent | None = None
    """ Current request's agent. """
    agents: Agent | list[Agent] | None = None
    """
    Receiver(s) used to fetch reference. It is different from :py:attr:`agent` as the latest is used to create references.

    This value is set in :py:meth:`dispatch` using :py:meth:`get_agents`. It will be either all request's user's
    agents (if :py:attr:`all_agents`) or only the active one.
    """

    reference_class = None
    """ Reference class (defaults to model's Reference). """

    def get_agents(self) -> Agent | list[Agent]:
        """Return value to use for :py:attr:`agents`."""
        return self.request.agents if self.all_agents else self.request.agent

    def get_reference_queryset(self):
        """Return reference queryset used to select objects."""
        return self.get_reference_class().objects.available(self.agents)

    def get_reference_class(self):
        """Return reference class used to create reference for object."""
        ref_class = self.reference_class
        if not ref_class:
            try:
                ref_class = getattr(self.model, "Reference")
            except AttributeError:
                raise ValueError("There is no Reference class provided for this model nor this view.")
        if not inspect.isclass(ref_class) or not issubclass(ref_class, Reference):
            raise ValueError(f"{ref_class} is not a Reference subclass.")
        return ref_class

    def get_queryset(self):
        """Get Object queryset based get_reference_queryset."""
        refs = self.get_reference_queryset()
        return super().get_queryset().refs(refs)

    def dispatch(self, request, *args, **kwargs):
        self.agents = self.get_agents()
        self.agent = request.agent
        return super().dispatch(request, *args, **kwargs)


class ObjectPermissionMixin(ObjectMixin):
    """
    Mixin providing access filtering based on reference and user's permission, using :py:attr:`can` attribute.
    """

    can: CanMany
    """ Capability permission(s) required to display the view.

    A string with Permission codename. ContentType will be matched \
    against current Capability's target :py:class:`.object.Object`.
    """

    @staticmethod
    @cache
    def _get_can_all_q(reference_class, can: CanMany | None = None) -> list[Q]:
        """Retun Q objects for filtering reference based on provided ``can``
        attribute.

        This method uses :py:func:`functools.cache` in order to optimize
        queryset building. This assumes that :py:attr:`can` will not change
        accross different view instances.
        """
        return reference_class.objects.can_all_q(can)

    def get_can_all_q(self) -> list[Q]:
        """Retun Q objects for filtering reference based on :py:attr:`can` attribute."""
        cls = self.get_reference_class()
        return self._get_can_all_q(cls, self.can)

    def get_reference_queryset(self):
        """Return queryset for references."""
        query = super().get_reference_queryset()

        if self.can:
            all_q = self.get_can_all_q()
            for q in all_q:
                query = query.filter(q)
        return query


class SingleObjectMixin(ObjectPermissionMixin):
    """Detail mixin used to retrieve Object detail.

    Note: user's reference is fetched from `get_object`, not `get_queryset`.
    """

    lookup_url_kwargs = "uuid"
    """ URL's kwargs argument used to retrieve reference uuid. """

    def get_reference_queryset(self):
        uuid = self.kwargs[self.lookup_url_kwargs]
        return super().get_reference_queryset().filter(uuid=uuid)

    def get_object(self):
        query = self.get_queryset()
        return get_object_or_404(query)


class ObjectListMixin(ObjectPermissionMixin):
    can = "view"


class ObjectDetailMixin(SingleObjectMixin):
    can = "view"


class ObjectCreateMixin(ObjectPermissionMixin):
    can = "add"

    def create_reference(self, emitter: Agent, target: Object):
        """Create root reference for the provided object."""
        cls = self.get_reference_class()
        ref = cls.create_root(emitter, target)
        setattr(target, "reference", ref)
        return ref


class ObjectUpdateMixin(SingleObjectMixin):
    can = "change"


class ObjectDeleteMixin(SingleObjectMixin):
    can = "delete"
