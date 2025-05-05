from django.contrib import admin
from caps.admin import register_object

from . import models


class ObjectAdmin(admin.ModelAdmin):
    list_display = ("pk", "name")


register_object(models.ConcreteObject, ObjectAdmin)
