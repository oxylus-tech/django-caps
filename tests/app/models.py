from django.db import models

from caps.models import Object

__all__ = ("ConcreteObject", "Access")


class ConcreteObject(Object):
    """This class is used to test object agains't concrete class."""

    detail_url_name = "concrete-detail"

    root_grants = {
        "caps_test.view_concreteobject": 4,
        "caps_test.change_concreteobject": 2,
    }

    name = models.CharField(max_length=16)


Access = ConcreteObject.Access


# class AbstractObject(Object):
#     name = models.CharField(max_length=16)
#
#     class Access(Access):
#         target = models.ForeignKey(ConcreteObject, models.CASCADE, related_name="_abstract")
#
#     class Meta:
#         abstract = True
#
#
# AbstractAccess = AbstractObject.Access
