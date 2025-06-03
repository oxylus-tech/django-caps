from functools import cached_property

from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404

from .. import permissions
from ..models import Agent, AccessQuerySet


__all__ = (
    "OwnedMixin",
    "OwnedPermissionMixin",
    "SingleOwnedMixin",
    "ByUUIDMixin",
    "AgentMixin",
    "AccessMixin",
)


class UserAgentMixin:
    """
    This mixin provides two cached properties providing user's agents.
    """

    @cached_property
    def agent(self) -> Agent:
        """Return user's agent."""
        return self.agents and self.agents[0]

    @cached_property
    def agents(self) -> list[Agent]:
        """
        Current user's agents (of his groups included).
        User's agent is the first of the list.
        """
        return Agent.objects.user(self.request.user).order_by("-user")


class OwnedMixin(UserAgentMixin):
    """
    Base mixin providing functionalities to work with :py:class:`~caps.models.object.Owned` model.

    It provides:

        - assign self's :py:attr:`agent` and :py:attr:`agents`
        - queryset to available :py:class:`~caps.models.access.Access`.

    """

    access_class = None
    """ Access class (defaults to model's Access). """

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
        """Get Owned queryset based get_access_queryset."""
        accesses = self.get_access_queryset()
        return super().get_queryset().available(self.agents, accesses)


# This class code is mostly taken from Django Rest Framework's permissions.DjangoModelPermissions
# Its code falls under the same license.
class OwnedPermissionMixin(OwnedMixin):
    """
    This mixin checks for object permission when ``get_object()`` is called. It raises a
    ``PermissionDenied`` or ``Http404`` if user does not have access to the object.
    """

    permissions = [permissions.OwnedPermissions]

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


class SingleOwnedMixin(OwnedMixin):
    """Detail mixin used to retrieve Owned detail.

    It requires subclass to have  a ``check_object_permissions`` method (
    eg by a child of :py:class:`OwnedPermissionMixin` or DRF APIView).
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

        q = Q(uuid=uuid, owner__in=self.agents)
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


class AgentMixin(ByUUIDMixin, UserAgentMixin, PermissionRequiredMixin):
    model = Agent


class AccessMixin(ByUUIDMixin, UserAgentMixin):
    """Mixin used by Access views and viewsets."""

    def get_queryset(self):
        # FIXME: owner shall be able to remove any access
        # a user can view/delete only access for which he is
        # either receiver or emitter.
        return super().get_queryset().agent(self.agents)
