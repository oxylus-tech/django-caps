from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets, mixins as mx
from rest_framework.decorators import action
from rest_framework.response import Response

from .. import models, serializers, permissions
from . import mixins


__all__ = (
    "OwnedViewSet",
    "AgentViewSet",
    "AccessViewSet",
)


class UserAgentMixin(mixins.UserAgentMixin):
    """Add ``agent`` and ``agents`` to serializers' contexts."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        return {**context, "agent": self.agent, "agents": self.agents}


class OwnedViewSet(UserAgentMixin, mixins.SingleOwnedMixin, viewsets.ModelViewSet):
    """
    This is the base viewset class for Owned models, running object permission checks.

    It also provides the :py:meth:`share` that allows a user to share an access to
    the object.
    """

    perms_map = {
        "share": ["%(app_label)s.change_%(model_name)s"],
    }

    share_serializer_class = serializers.ShareSerializer
    """ The serializer class used for the :py:meth:`share` action. """

    permission_classes = [permissions.OwnedPermissions]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_access_queryset(self):
        # disable access fetch
        if self.action == "share":
            return None
        return super().get_access_queryset()

    def get_queryset(self):
        if self.action == "share":
            return super().get_queryset().filter(owner__in=self.agents)
        return super().get_queryset()

    @action(detail=True, methods=["post"])
    def share(self, request, uuid=None):
        """Share object, returning the newly created Access.

        Example of request's POST data in YAML (see :py:meth:`~caps.models.access.Access.share` and :py:class:`~caps.serializers.ShareSerializer`):

        .. code-block:: yaml

            receiver: "agent-uuid"
            expiration: null
            grants:
                myapp.view_myobject: 1
                myapp.change_myobject: 0

        """
        obj = self.get_object()
        ser = self.share_serializer_class(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        access = obj.share(ser.validated_data["receiver"], ser.validated_data["grants"])

        # Get Access serializer from field `access`
        ser_cls = type(self.get_serializer_class()._declared_fields["access"])
        return Response(ser_cls(access).data, status=201)


class AccessViewSet(
    UserAgentMixin, mx.RetrieveModelMixin, mx.DestroyModelMixin, mx.ListModelMixin, viewsets.GenericViewSet
):
    """
    This viewset provides API to :py:class:`~caps.models.access.Access`.

    It ensures that:

        - Access can't be created
        - Access can't be updated
        - Access can only be shared, listed, retrieved, and destroyed.

    Note: no model nor queryset is provided by default, as Access is an abstract class and is dependent of the concrete Owned sub-model.
    """

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    filterset_fields = (
        "receiver__uuid",
        "emitter__uuid",
        "origin__uuid",
        "target__uuid",
    )

    share_serializer_class = serializers.ShareSerializer
    """ This specifies serializer class used for the :py:meth:`share` action. """
    serializer_class = serializers.AccessSerializer

    def get_queryset(self):
        query = super().get_queryset()
        if self.action == "share":
            return query.receiver(self.agents)
        return query.agent(self.agents)

    @action(detail=True, methods=["post"])
    def share(self, request, uuid=None):
        """Share object access to someone. See :py:meth:`OwnedViewSet.share` for more info."""
        access = self.get_object()
        ser = self.share_serializer_class(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        shared = access.share(ser.validated_data["receiver"], ser.validated_data["grants"])
        return Response(self.get_serializer_class()(shared).data, status=201)


class AgentViewSet(UserAgentMixin, viewsets.ModelViewSet):
    """Viewset provides API for :py:class:`~caps.models.agent.Agent`.

    Provides an extra API endpoint ``user`` returning user's agents (:py:meth:`user`).
    """

    model = models.Agent
    queryset = models.Agent.objects.all()
    serializer_class = serializers.AgentSerializer
    permissions = [permissions.DjangoModelPermissions]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    filterset_fields = ("group", "user")
    search_fields = ("group__name", "user__name")

    @action(detail=False, methods=["GET"])
    def user(self, *_):
        """
        Return request agents for user using ``GET['user']``.
        When parameter is not provided, it uses current user.
        """
        if userId := self.request.GET.get("user"):
            if not self.request.user.has_perm("caps.view_agent") and userId != self.request.user.id:
                raise PermissionDenied("Not allowed")

            user = get_object_or_404(User.objects.all(), pk=userId)
            agents = self.queryset.user(user)
        else:
            agents = self.agents

        return Response(self.get_serializer_class()(instance=agents, many=True).data)
