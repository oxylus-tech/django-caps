from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404

from .. import permissions
from ..models import Agent, AccessQuerySet


__all__ = (
    "ObjectMixin",
    "ObjectPermissionMixin",
    "SingleObjectMixin",
    "ByUUIDMixin",
    "AgentMixin",
    "AccessMixin",
)


class ObjectMixin:
    """
    Base mixin providing functionalities to work with :py:class:`~caps.models.object.Object` model.

    It provides:

        - assign self's :py:attr:`agent` and :py:attr:`agents`
        - queryset to available :py:class:`~caps.models.access.Access`.

    """

    all_agents: bool = False
    """
    When this parameter is ``True``, it filter object's access using
    all user's assigned agents instead of only the current one. See :py:attr:`agents` for more information.
    """

    agent: Agent | None = None
    """ Current request's agent. """
    agents: Agent | list[Agent] | None = None
    """
    Receiver(s) used to fetch access. It is different from :py:attr:`agent` as the latest is used to create accesses.

    This value is set in :py:meth:`dispatch` using :py:meth:`get_agents`. It will be either all request's user's
    agents (if :py:attr:`all_agents`) or only the active one.
    """

    access_class = None
    """ Access class (defaults to model's Access). """

    def get_agents(self) -> Agent | list[Agent]:
        """Return value to use for :py:attr:`agents`."""
        return self.request.agents if self.all_agents else self.request.agent

    def get_access_queryset(self) -> AccessQuerySet | None:
        """Return queryset for accesses."""
        query = None
        if model := getattr(self, "model", None):
            query = model.Access.objects.all()
        else:
            query = getattr(self, "queryset", None)
            if query is not None:
                query = query.model.Access.objects.all()

        if query is not None:
            return query.select_related("receiver")
        return None

    def get_queryset(self):
        """Get Object queryset based get_access_queryset."""
        accesses = self.get_access_queryset()
        return super().get_queryset().available(self.request.agents, accesses)

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

    def check_object_permissions(self, request, obj):
        if perms := self.get_permissions():
            allowed = any(p.has_object_permission(request, self, obj) for p in perms)
            if not allowed:
                raise PermissionDenied(f"Permission not allowed for {self.request.method} on this object.")

    def get_permissions(self):
        return [p() for p in self.permissions]


class SingleObjectMixin(ObjectMixin):
    """Detail mixin used to retrieve Object detail.

    It requires subclass to have  a ``check_object_permissions`` method (
    eg by a child of :py:class:`ObjectPermissionMixin` or DRF APIView).
    """

    lookup_url_kwarg = "uuid"
    """ URL's kwargs argument used to retrieve access uuid. """

    def get_access_queryset(self):
        """When ``uuid`` GET argument is provided, filter accesses on it."""
        query = super().get_access_queryset()
        if query is not None:
            if uuid := self.kwargs.get(self.lookup_url_kwarg):
                return query.filter(uuid=uuid)
        return query

    def get_object(self):
        uuid = self.kwargs[self.lookup_url_kwarg]

        q = Q(uuid=uuid, owner__in=self.request.agents)
        if accesses := self.get_access_queryset():
            q |= Q(accesses__in=accesses)

        obj = get_object_or_404(self.get_queryset(), q)
        self.check_object_permissions(self.request, obj)
        return obj


# ---- Other mixins
class ByUUIDMixin:
    """Fetch a model by UUID."""

    lookup_url_kwarg = "uuid"
    """ URL's kwargs argument used to retrieve access uuid. """

    def get_object(self):
        return get_object_or_404(self.get_queryset(), uuid=self.kwargs[self.lookup_url_kwarg])


class AgentMixin(ByUUIDMixin, PermissionRequiredMixin):
    model = Agent


class AccessMixin(ByUUIDMixin):
    """Mixin used by Access views and viewsets."""

    def get_queryset(self):
        # FIXME: owner shall be able to remove any access
        # a user can view/delete only access for which he is
        # either receiver or emitter.
        return super().get_queryset().agent(self.request.agents)
