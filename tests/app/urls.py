from django.urls import path

from caps import views
from . import models


urlpatterns = [
    path("/concrete/", views.ObjectListView.as_view(model=models.ConcreteObject), name="concrete-list"),
    path("/concrete/<uuid:uuid>/", views.ObjectDetailView.as_view(model=models.ConcreteObject), name="concrete-detail"),
    path("/concrete/create/", views.ObjectCreateView.as_view(model=models.ConcreteObject), name="concrete-create"),
    path(
        "/concrete/update/<uuid:uuid>",
        views.ObjectUpdateView.as_view(model=models.ConcreteObject),
        name="concrete-update",
    ),
]
