import logging
from django.apps import AppConfig

__all__ = ("CapsConfig",)

logger = logging.getLogger()


class CapsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "caps"
    label = "caps"

    def ready(self):
        """Enforce permissions validation at boot-up."""
        from . import signals

        signals.create_group_agent
