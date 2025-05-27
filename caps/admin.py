from django.contrib import admin

from . import models


__all__ = ("AgentAdmin", "ReferenceAdmin", "register_object")


@admin.register(models.Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "group", "is_default")
    list_filter = ("group",)
    fields = ("uuid", "user", "group", "is_default")
    readonly_fields = ("uuid",)


class ReferenceAdmin(admin.ModelAdmin):
    list_display = ("uuid", "target", "origin", "emitter", "receiver", "expiration", "depth")
    list_filter = ("depth",)
    fields = ("uuid", "target", "origin", "depth", "emitter", "receiver", "expiration", "grants")


def register_object(obj_class: type[models.Object], admin_class: type[admin.ModelAdmin]):
    """
    Register model admin for Object class, its Capability and Reference.

    It uses:

        - :py:class:`BaseCapabilityInline`: inline Capability in Reference admin;
        - :py:class:`BaseReferenceAdmin`: to register Reference admin;
        - :py:class:`ObjectAdmin` (by default): to register Object admin;

    :param obj_class: the object class
    :param admin_class: ObjectAdmin class to register object class.
    """

    admin.site.register(obj_class, admin_class)
    admin.site.register(obj_class.Reference, ReferenceAdmin)
