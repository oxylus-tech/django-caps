from django.db import models

from caps.models import Owned

__all__ = ("ConcreteOwned", "Access")


class ConcreteOwned(Owned):
    """This class is used to test object agains't concrete class."""

    detail_url_name = "concrete-detail"

    root_grants = {
        "caps_test.view_concreteowned": 4,
        "caps_test.change_concreteowned": 2,
    }

    name = models.CharField(max_length=16)


Access = ConcreteOwned.Access


# class AbstractOwned(Owned):
#     name = models.CharField(max_length=16)
#
#     class Access(Access):
#         target = models.ForeignKey(ConcreteOwned, models.CASCADE, related_name="_abstract")
#
#     class Meta:
#         abstract = True
#
#
# AbstractAccess = AbstractOwned.Access
