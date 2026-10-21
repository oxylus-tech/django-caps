from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.TEST:
    urlpatterns.append(
        path("test/", include("tests.app.urls")),
    )
