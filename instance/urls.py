from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
]

if getattr(settings, "TEST", False):
    urlpatterns.append(
        path("test/", include("tests.app.urls")),
    )
