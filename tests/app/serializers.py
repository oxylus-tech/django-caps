from caps.serializers import ObjectSerializer

from . import models


__all__ = ("ConcreteObjectSerializer",)


class ConcreteObjectSerializer(ObjectSerializer):
    class Meta:
        model = models.ConcreteObject
        fields = "__all__"
