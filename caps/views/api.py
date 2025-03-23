from rest_framework import generics, viewsets

from . import mixins


class ObjectListAPIView(mixins.ObjectListMixin, generics.ListAPIView):
    pass


class ObjectRetrieveAPIView(mixins.ObjectDetailMixin, generics.DetailAPIView):
    pass


class ObjectCreateAPIView(mixins.ObjectCreateMixin, generics.CreateAPIView):
    pass


class ObjectUpdateAPIView(mixins.ObjectUpdateMixin, generics.UpdateAPIView):
    pass


class ObjectDestroyAPIView(mixins.ObjectDeleteMixin, generics.DestroyAPIView):
    pass


class ViewSetMixin(mixins.SingleObjectMixin):
    actions = {
        "list": ObjectListAPIView.actions,
        "retrieve": ObjectRetrieveAPIView.actions,
        "create": ObjectCreateAPIView.actions,
        "update": ObjectUpdateAPIView.actions,
        "destroy": ObjectDestroyAPIView.actions,
    }
    """ Map of ViewSet actions to references' ones. """

    def get_action(self):
        return self.actions.get(self.action)


class GenericViewSet(ViewSetMixin, viewsets.GenericViewSet):
    pass


class ModelViewSet(ViewSetMixin, viewsets.ModelViewSet):
    pass
