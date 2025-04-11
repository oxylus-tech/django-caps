from django.db import models

from caps.models import Object

__all__ = ("ConcreteObject", "Reference", "Capability")


class ConcreteObject(Object):
    """This class is used to test object agains't concrete class."""

    detail_url_name = "concrete-detail"

    name = models.CharField(max_length=16)


Reference = ConcreteObject.Reference
Capability = ConcreteObject.Capability


# class AbstractObject(Object):
#     name = models.CharField(max_length=16)
#
#     class Reference(Reference):
#         target = models.ForeignKey(ConcreteObject, models.CASCADE, related_name="_abstract")
#
#     class Meta:
#         abstract = True
#
#
# AbstractReference = AbstractObject.Reference
