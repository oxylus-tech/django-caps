from django.contrib.auth.backends import BaseBackend
from . import models


__all__ = ("PermissionsBackend",)


class PermissionsBackend(BaseBackend):
    """
    Provide object permission backend using the capabilities system.

    The check is only run on :py:class:`~.models.owned.Owned` and
    :py:class:`~/models.access.Access` instances.

    You can add it to the ``AUTHENTICATION_BACKENDS`` setting, as:

    ..code-block:: python

        AUTHENTICATION_BACKENDS = [
            "django.contrib.auth.backends.ModelBackend",
            "caps.backends.PermissionsBackend",
        ]

    """

    def has_perm(self, user, perm, obj=None) -> bool:
        if isinstance(obj, (models.Owned, models.Access)):
            return obj.has_perm(user, perm)
        return False

    def get_all_permissions(self, user, obj=None) -> set[str]:
        if isinstance(obj, (models.Owned, models.Access)):
            return obj.get_all_permissions(user)
        return set()
