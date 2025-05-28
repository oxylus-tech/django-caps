from django.contrib.auth.backends import BaseBackend
from . import models


__all__ = ("PermissionsBackend",)


class PermissionsBackend(BaseBackend):
    """
    Provide permission backend using capabilities system.

    It will only test permissions on Object and Reference subclass.
    """

    def has_perm(self, user, perm, obj=None) -> bool:
        if isinstance(obj, (models.Object, models.Reference)):
            return obj.has_perm(user, perm)
        return False

    def get_all_permissions(self, user, obj=None) -> set[str]:
        if isinstance(obj, (models.Object, models.Reference)):
            return obj.get_all_permissions(user)
        return set()
