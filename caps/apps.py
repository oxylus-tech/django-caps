from django.apps import AppConfig

__all__ = ("CapsConfig",)


class CapsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "caps"
    label = "caps"
