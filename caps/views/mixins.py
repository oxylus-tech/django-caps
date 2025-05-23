import inspect

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404

from .. import permissions
from ..models import Agent, Object, Reference


__all__ = (
    "ObjectMixin",
    "ObjectPermissionMixin",
    "SingleObjectMixin",
    "ObjectCreateMixin",
    "ByUUIDMixin",
    "AgentMixin",
    "ReferenceMixin",
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
        return self.get_reference_class().objects.available(self.agents).select_related("receiver")

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


# This class code is mostly taken from Django Rest Framework's permissions.DjangoModelPermissions
# Its code falls under the same license.
class ObjectPermissionMixin(ObjectMixin):
    """
    This mixin checks for object permission when ``get_object()`` is called. It raises a
    ``PermissionDenied`` or ``Http404`` if user does not have access to the object.
    """

    permissions = [permissions.ObjectPermissions]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(obj)
        return obj

    def check_object_permissions(self, obj):
        if perms := self.get_permissions():
            allowed = any(p.has_object_permission(self.request, self, obj) for p in perms)
            if not allowed:
                raise PermissionDenied(f"Permission not allowed for {self.request.method} on this object.")

    def get_permissions(self):
        return [p() for p in self.permissions]


class SingleObjectMixin(ObjectPermissionMixin):
    """Detail mixin used to retrieve Object detail.

    Note: user's reference is fetched from `get_reference_queryset`, not `get_queryset`.
    """

    lookup_url_kwarg = "uuid"
    """ URL's kwargs argument used to retrieve reference uuid. """

    def get_reference_queryset(self):
        # we ensure selected object will be assigned to the right reference.
        uuid = self.kwargs[self.lookup_url_kwarg]
        return super().get_reference_queryset().filter(uuid=uuid)

    def get_object(self):
        uuid = self.kwargs[self.lookup_url_kwarg]
        return get_object_or_404(self.get_queryset(), references__uuid=uuid)


class ObjectCreateMixin(ObjectMixin):
    can = "add"

    def create_reference(self, emitter: Agent, target: Object):
        """Create root reference for the provided object."""
        cls = self.get_reference_class()
        ref = cls.create_root(emitter, target)
        setattr(target, "reference", ref)
        return ref


# ---- Other mixins
class ByUUIDMixin:
    """Fetch a model by UUID."""

    lookup_url_kwarg = "uuid"
    """ URL's kwargs argument used to retrieve reference uuid. """

    def get_object(self):
        return get_object_or_404(self.get_queryset(), uuid=self.kwargs[self.lookup_url_kwarg])


class AgentMixin(ByUUIDMixin, PermissionRequiredMixin):
    model = Agent


class ReferenceMixin(ByUUIDMixin):
    """Mixin used by Reference views and viewsets."""

    def get_queryset(self):
        # a user can view/delete only mixin for which he is
        # either receiver or emitter.
        return super().get_queryset().agent(self.request.agents)
