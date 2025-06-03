from caps import views

from . import models
from .serializers import ConcreteOwnedSerializer


class OwnedViewSet(views.OwnedViewSet):
    serializer_class = ConcreteOwnedSerializer
    queryset = models.ConcreteOwned.objects.all()


class AccessViewSet(views.AccessViewSet):
    queryset = models.Access.objects.all()
