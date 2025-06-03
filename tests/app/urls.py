from django.urls import include, path
from rest_framework.routers import SimpleRouter

from caps import urls
from . import models, views


router = SimpleRouter()
router.register("object", views.OwnedViewSet)
router.register("object-access", views.AccessViewSet)


urlpatterns = urls.get_object_paths(models.ConcreteOwned, basename="concrete") + [path("api/", include(router.urls))]
