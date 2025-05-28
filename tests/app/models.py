from django.db import models

from caps.models import Object

__all__ = ("ConcreteObject", "Reference")


class ConcreteObject(Object):
    """This class is used to test object agains't concrete class."""

    detail_url_name = "concrete-detail"

    root_grants = {
        "caps_test.view_concreteobject": 4,
        "caps_test.change_concreteobject": 2,
    }

    name = models.CharField(max_length=16)


Reference = ConcreteObject.Reference


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
