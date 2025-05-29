from caps import views

from . import models
from .serializers import ConcreteObjectSerializer


class ObjectViewSet(views.ObjectViewSet):
    serializer_class = ConcreteObjectSerializer
    queryset = models.ConcreteObject.objects.all()


class AccessViewSet(views.AccessViewSet):
    queryset = models.Access.objects.all()
