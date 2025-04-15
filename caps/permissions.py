from rest_framework import permissions


__all__ = ("DjangoModelPermissions",)


class DjangoModelPermissions(permissions.DjangoModelPermissions):
    """Subclass DRF DjangoModelPermissions in order to add "view" permission on GET request."""

    perms_map = {
        **permissions.DjangoModelPermissions,
        "GET": ["%(app_label)s.view_%(model_name)s"],
    }
