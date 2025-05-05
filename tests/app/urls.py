from caps import urls
from . import models


urlpatterns = urls.get_object_paths(models.ConcreteObject, basename="concrete")
