from django.contrib import admin

from . import models


__all__ = ("AgentAdmin", "AccessAdmin", "register_object")


@admin.register(models.Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "group")
    list_filter = ("group",)
    fields = ("uuid", "user", "group")
    readonly_fields = ("uuid",)


class AccessAdmin(admin.ModelAdmin):
    list_display = ("uuid", "target", "origin", "emitter", "receiver", "expiration")
    fields = ("uuid", "target", "origin", "emitter", "receiver", "expiration", "grants")


def register_object(obj_class: type[models.Owned], admin_class: type[admin.ModelAdmin]):
    """
    Register model admin for Owned class, its Capability and Access.

    It uses:

        - :py:class:`BaseCapabilityInline`: inline Capability in Access admin;
        - :py:class:`BaseAccessAdmin`: to register Access admin;
        - :py:class:`OwnedAdmin` (by default): to register Owned admin;

    :param obj_class: the object class
    :param admin_class: OwnedAdmin class to register object class.
    """

    admin.site.register(obj_class, admin_class)
    admin.site.register(obj_class.Access, AccessAdmin)
