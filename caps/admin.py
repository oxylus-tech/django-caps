from django.contrib import admin

from . import models


__all__ = ("AgentAdmin", "AccessAdmin", "register_object")


@admin.register(models.Agent)
class AgentAdmin(admin.ModelAdmin):
    """Admin interface for an :py:class:`~.models.agent.Agent`."""

    list_display = ("uuid", "user", "group")
    list_filter = ("group",)
    fields = ("uuid", "user", "group")
    readonly_fields = ("uuid",)


class AccessAdmin(admin.ModelAdmin):
    """Admin interface for an :py:class:`~.models.access.Access`."""

    list_display = ("uuid", "target", "origin", "emitter", "receiver", "expiration")
    fields = ("uuid", "target", "origin", "emitter", "receiver", "expiration", "grants")


def register_object(obj_class: type[models.Owned], admin_class: type[admin.ModelAdmin]):
    """
    This helper function register an Owned class to a django's ModelAdmin.
    It will register the concrete model's :py:class:`~.models.access.Access` model
    to using :py:class:`AccessAdmin`.

    :param obj_class: the object class
    :param admin_class: OwnedAdmin class to register object class.
    """

    admin.site.register(obj_class, admin_class)
    admin.site.register(obj_class.Access, AccessAdmin)
