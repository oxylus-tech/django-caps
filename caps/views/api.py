from rest_framework import status, viewsets, mixins as mx
from rest_framework.decorators import action
from rest_framework.response import Response

from .. import models, serializers, permissions
from . import mixins


__all__ = (
    "ObjectViewSet",
    "AgentViewSet",
    "ReferenceViewSet",
)


class ObjectViewSet(mixins.ObjectMixin, viewsets.ModelViewSet):
    """
    This is the base mixin handling permissions check for django-caps.
    """

    share_serializer_class = serializers.ShareSerializer
    """ This specifies serializer class used for the :py:meth:`share` action. """

    permission_classes = [permissions.ObjectPermissions]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self):
        if self.action == "share":
            return super().get_queryset().filter(owner__in=self.request.agents)
        return super().get_queryset()

    @action(detail=True, methods=["post"])
    def share(self, request, uuid=None):
        """Share object.

        Example of request's POST data in YAML (see :py:meth:`~caps.models.reference.Reference.share` and :py:class:`~caps.serializers.ShareSerializer`):

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
        obj.reference = obj.share(ser.validated_data["receiver"], ser.validated_data["grants"])
        return Response(self.get_serializer_class()(obj).data)


class AgentViewSet(viewsets.ModelViewSet):
    """Viewset provides API for :py:class:`~caps.models.agent.Agent`."""

    model = models.Agent
    queryset = models.Agent.objects.all()
    permissions = [permissions.DjangoModelPermissions]
    filterset_fields = ("group", "user", "user__group")


class ReferenceViewSet(mx.RetrieveModelMixin, mx.DestroyModelMixin, mx.ListModelMixin, viewsets.GenericViewSet):
    """
    This viewset provides API to :py:class:`~caps.models.reference.Reference`.

    It ensures that:

        - Reference can't be created
        - Reference can't be updated
        - Reference can only be shared, listed, retrieved, and destroyed.

    Note: no model nor queryset is provided by default, as Reference is an abstract class and is dependent of the concrete Object sub-model.
    """

    lookup_field = "uuid"
    lookup_url_kwargs = "uuid"
    filterset_fields = (
        "receiver__uuid",
        "emitter__uuid",
        "origin__uuid",
        "target__uuid",
    )

    share_serializer_class = serializers.ShareSerializer
    """ This specifies serializer class used for the :py:meth:`share` action. """
    serializer_class = serializers.ReferenceSerializer

    def get_queryset(self):
        query = super().get_queryset()
        if self.action == "share":
            return query.receiver(self.request.agents)
        return query.agent(self.request.agents)

    @action(detail=True, methods=["post"])
    def share(self, request, uuid=None):
        """Share object reference to someone. See :py:meth:`ObjectViewSet.share` for more info."""
        ref = self.get_object()
        ser = self.share_serializer_class(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        shared = ref.share(ser.validated_data["receiver"], ser.validated_data["grants"])
        return Response(self.get_serializer_class()(shared).data)
