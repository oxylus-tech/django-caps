from django.contrib import admin
from caps.admin import register_object

from . import models


class OwnedAdmin(admin.ModelAdmin):
    list_display = ("pk", "name")


register_object(models.ConcreteOwned, OwnedAdmin)
