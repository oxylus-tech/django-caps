from caps import views

from . import models
from .serializers import ConcreteObjectSerializer


class ObjectViewSet(views.ObjectViewSet):
    serializer_class = ConcreteObjectSerializer
    queryset = models.ConcreteObject.objects.all()


class ReferenceViewSet(views.ReferenceViewSet):
    queryset = models.Reference.objects.all()
