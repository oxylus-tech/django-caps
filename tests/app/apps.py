from django.apps import AppConfig


class CapsTestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.app"
    label = "caps_test"
