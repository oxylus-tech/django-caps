from django.contrib import admin

from . import models


__all__ = ("AgentAdmin", "AccessAdmin", "register_object")


@admin.register(models.Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "group", "is_default")
    list_filter = ("group",)
    fields = ("uuid", "user", "group", "is_default")
    readonly_fields = ("uuid",)


class AccessAdmin(admin.ModelAdmin):
    list_display = ("uuid", "target", "origin", "emitter", "receiver", "expiration")
    fields = ("uuid", "target", "origin", "emitter", "receiver", "expiration", "grants")


def register_object(obj_class: type[models.Object], admin_class: type[admin.ModelAdmin]):
    """
    Register model admin for Object class, its Capability and Access.

    It uses:

        - :py:class:`BaseCapabilityInline`: inline Capability in Access admin;
        - :py:class:`BaseAccessAdmin`: to register Access admin;
        - :py:class:`ObjectAdmin` (by default): to register Object admin;

    :param obj_class: the object class
    :param admin_class: ObjectAdmin class to register object class.
    """

    admin.site.register(obj_class, admin_class)
    admin.site.register(obj_class.Access, AccessAdmin)
