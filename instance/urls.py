from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("test/", include("tests.app.urls")),
    path("admin/", admin.site.urls),
]
