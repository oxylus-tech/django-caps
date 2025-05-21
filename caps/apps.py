import logging
from django.apps import AppConfig

__all__ = ("CapsConfig",)

logger = logging.getLogger()


class CapsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "caps"
    label = "caps"


#     def ready(self):
#         """ Enforce permissions validation at boot-up. """
#         from .models import Object
#         self.check_root_reference_grants(Object)
#
#     def check_root_reference_grants(self, model):
#         try:
#             model.check_root_reference_grants()
#         except ValueError as err:
#             logger.warn(err)
#
#         for sub in model.__subclasses__():
#             self.check_root_reference_grants(sub)
