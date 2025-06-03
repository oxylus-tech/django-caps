from caps.serializers import OwnedSerializer

from . import models


__all__ = ("ConcreteOwnedSerializer",)


class ConcreteOwnedSerializer(OwnedSerializer):
    class Meta:
        model = models.ConcreteOwned
        fields = "__all__"
