from django.db.models import Q

from rest_framework import generics, status, viewsets, mixins as mx
from rest_framework.decorators import action
from rest_framework.response import Response

from .. import models, serializers
from ..models.capability import CanMany
from . import mixins, permissions


__all__ = (
    "ObjectListAPIView",
    "ObjectRetrieveAPIView",
    "ObjectCreateAPIView",
    "ObjectUpdateAPIView",
    "ObjectDestroyAPIView",
    "ObjectViewSet",
    "AgentViewSet",
    "ReferenceViewSet",
)


class ObjectCreateAPIMixin(mixins.ObjectCreateMixin):
    def perform_create(self, serializer):
        super().perform_create(serializer)
        self.create_reference(self.agent, serializer.instance)


class ObjectListAPIView(mixins.ObjectListMixin, generics.ListAPIView):
    pass


class ObjectRetrieveAPIView(mixins.ObjectDetailMixin, generics.RetrieveAPIView):
    pass


class ObjectCreateAPIView(ObjectCreateAPIMixin, generics.CreateAPIView):
    pass


class ObjectUpdateAPIView(mixins.ObjectUpdateMixin, generics.UpdateAPIView):
    pass


class ObjectDestroyAPIView(mixins.ObjectDeleteMixin, generics.DestroyAPIView):
    pass


class ObjectViewSet(ObjectCreateAPIMixin, mixins.SingleObjectMixin, viewsets.ModelViewSet):
    """
    This is the base mixin handling permission check for django-caps.

    It provides mapping between actions and specific permissions.

    """

    can: dict[str, CanMany] = {
        "list": ObjectListAPIView.can,
        "retrieve": ObjectRetrieveAPIView.can,
        "create": ObjectCreateAPIView.can,
        "update": ObjectUpdateAPIView.can,
        "destroy": ObjectDestroyAPIView.can,
    }
    """ Map of ViewSet actions to references' ones. """

    def get_can_all_q(self) -> list[Q]:
        """Return Q object for filtering reference on :py:attr:`can` attribute and current request action."""
        cls = self.get_reference_class()
        can = self.can and self.can.get(self.action)
        return self._get_can_all_q(cls, can) if can else []


class AgentViewSet(viewsets.ModelViewSet):
    """Viewset provides API for :py:class:`~caps.models.agent.Agent`."""

    model = models.Agent
    queryset = models.Agent.all()
    permissions = [permissions.DjangoModelPermissions]


class ReferenceViewSet(mx.RetrieveModelMixin, mx.DestroyModelMixin, mx.ListModelMixin, viewsets.GenericViewSet):
    """
    This viewset provides API to :py:class:`~caps.models.reference.Reference`.

    It ensures that:

        - Reference can't be created
        - Reference can't be updated
        - Reference can only be derived, list, retrieve, and destroyed.

    Note: no model nor queryset is provided by default, as Reference is an abstract class and is dependent of the concrete Object sub-model.
    """

    derive_serializer_class = serializers.DeriveSerializer
    """ This specifies serializer class used for the :py:meth:`derive` action. """
    serializer_class = serializers.ReferenceSerializer

    def get_queryset(self):
        query = super().get_queryset().prefetch_related("capabilities")
        if self.action == "derive":
            return query.emitter(self.request.agents)
        return query.agent(self.request.agents)

    @action(detail=True, methods=["post"])
    def derive(self, request, pk=None):
        """Derive reference from current one.

        Example of request's POST data in YAML (see :py:meth:`~caps.models.reference.Reference.derive`,
        :py:type:`~caps.models.capability_set.CapabilitySet.Cap`, and :py:class:`~caps.serializers.DeriveSerializer`):

        .. code-block:: yaml

            receiver: "agent-uuid"
            caps:
                - [12, 1]
                - 1
        """
        ref = self.get_object()
        derive_ser = self.derive_serializer_class(data=request.data)
        if not derive_ser.is_valid():
            return Response(derive_ser.errors, status=status.HTTP_400_BAD_REQUEST)

        derived = ref.derive(derive_ser.validated_data["receiver"], derive_ser.validated_data["caps"])
        return Response(self.get_serializer_class(derived).data)
