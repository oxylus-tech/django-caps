from django.db import models

from caps.models import Owned, OwnedTreeNode as _OwnedTreeNode


__all__ = ("ConcreteOwned", "Access", "OwnedTreeNode")


class ConcreteOwned(Owned):
    """This class is used to test object agains't concrete class."""

    detail_url_name = "concrete-detail"

    root_grants = {
        "caps_test.view_concreteowned": 4,
        "caps_test.change_concreteowned": 2,
    }

    name = models.CharField(max_length=16)


Access = ConcreteOwned.Access


class OwnedTreeNode(_OwnedTreeNode):
    name = models.CharField(max_length=32, default="")
