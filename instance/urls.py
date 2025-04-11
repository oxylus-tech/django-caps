from django.urls import path, include

urlpatterns = [path("test", include("tests.app.urls"))]
