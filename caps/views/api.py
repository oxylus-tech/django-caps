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


class ObjectViewSet(mixins.ObjectCreateMixin, viewsets.ModelViewSet):
    """
    This is the base mixin handling permissions check for django-caps.
    """

    permissions = [permissions.ObjectPermissions]
    lookup_field = "reference__uuid"
    lookup_url_kwarg = "uuid"

    def perform_create(self, serializer):
        """Ensure a root reference is created when the Object is saved."""
        super().perform_create(serializer)
        self.create_reference(self.agent, serializer.instance)

    def get_reference_queryset(self):
        # here is a little similar to SingleObjectMixin but
        # we have to do it only when action is detail
        query = super().get_reference_queryset()
        if self.detail:
            uuid = self.kwargs[self.lookup_url_kwarg]
            query = query.filter(uuid=uuid)
        return query


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
        - Reference can only be derived, listed, retrieved, and destroyed.

    Note: no model nor queryset is provided by default, as Reference is an abstract class and is dependent of the concrete Object sub-model.
    """

    lookup_field = "uuid"
    lookup_url_kwargs = "uuid"
    filterset_fields = (
        "receiver__uuid",
        "emitter__uuid",
        "origin__uuid",
    )

    derive_serializer_class = serializers.DeriveSerializer
    """ This specifies serializer class used for the :py:meth:`derive` action. """
    serializer_class = serializers.ReferenceSerializer

    def get_queryset(self):
        query = super().get_queryset()
        if self.action == "derive":
            return query.receiver(self.request.agents)
        return query.agent(self.request.agents)

    @action(detail=True, methods=["post"])
    def derive(self, request, pk=None):
        """Derive reference from current one.

        Example of request's POST data in YAML (see :py:meth:`~caps.models.reference.Reference.derive`,
        :py:type:`~caps.models.capability_set.CapabilitySet.Cap`, and :py:class:`~caps.serializers.DeriveSerializer`):

        .. code-block:: yaml

            receiver: "agent-uuid"
            capabilities:
                - ["myapp.view_myobject", 1]
                - ["myapp.change_myobject", 0]
        """
        ref = self.get_object()
        derive_ser = self.derive_serializer_class(data=request.data)
        if not derive_ser.is_valid():
            return Response(derive_ser.errors, status=status.HTTP_400_BAD_REQUEST)

        derived = ref.derive(derive_ser.validated_data["receiver"], derive_ser.validated_data["capabilities"])
        return Response(self.get_serializer_class()(derived).data)
