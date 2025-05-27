from django.urls import include, path
from rest_framework.routers import SimpleRouter

from caps import urls
from . import models, views


router = SimpleRouter()
router.register("object", views.ObjectViewSet)
router.register("object-reference", views.ReferenceViewSet)


urlpatterns = urls.get_object_paths(models.ConcreteObject, basename="concrete") + [path("api/", include(router.urls))]
