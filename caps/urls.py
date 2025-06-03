from typing import Any

from django.urls import path

from . import models, views


def get_object_paths(
    obj_class: type[models.Owned],
    url_paccessix: str | None = None,
    kwargs: dict[str, Any] | None = None,
    basename: str = "",
    accesses: bool = False,
    access_kwargs: dict[str, Any] | None = None,
) -> list[path]:
    """
    Return Django paths for the provided object class, including to edit access (:py:func:`get_access_path`).

    .. code-block:: python

        from caps.urls import get_object_paths
        from . import models

        urlpatterns = (
            get_object_paths(models.Post, 'post')
        )

    :param obj_class: the object model class;
    :param url_paccessix: url base path (default to model name);
    :param kwargs: ``as_view`` kwargs, by view kind (list, detail, etc.)
    :param basename: use this as url's basename (default to model name)
    :param accesses: if True, generate path for Owned's Access using default view (see :py:mod:`caps.views.common`)
    :param access_kwargs: ``kwargs`` argument passed down to :py:func:`get_access_class`.

    :return: a list of path
    """
    if not basename:
        basename = obj_class._meta.model_name
    if url_paccessix is None:
        url_paccessix = basename
    kwargs = kwargs or {}
    return _get_paths(
        obj_class,
        basename,
        [
            ("list", views.OwnedListView, url_paccessix),
            ("detail", views.OwnedDetailView, f"{url_paccessix}/<uuid:uuid>"),
            ("create", views.OwnedCreateView, f"{url_paccessix}/create"),
            ("update", views.OwnedUpdateView, f"{url_paccessix}/<uuid:uuid>/update"),
            ("delete", views.OwnedDeleteView, f"{url_paccessix}/<uuid:uuid>/delete"),
        ],
        kwargs,
    ) + get_access_paths(obj_class.Access, f"{url_paccessix}/access", kwargs=access_kwargs)


def get_access_paths(
    access_class: type[models.Access],
    url_paccessix: str = "access",
    kwargs: dict[str, Any] | None = None,
    basename: str = "",
) -> list[path]:
    """
    Return Django paths for the provided access class.

    Created path for views: ``list``, ``detail``, ``delete``.

    The path will have names such as (for a model named ``contact``): ``contact-access-list``.

    :param access_class: Access class
    :param kwargs: ``as_view`` extra arguments by view type
    :param basename: use this a base name for url, instead of ``{object_model_name}-access``.
    :returns: list of path
    """
    if not basename:
        obj_class = access_class.get_object_class()
        basename = f"{obj_class._meta.model_name}-access"
    return _get_paths(
        access_class,
        basename,
        [
            ("list", views.AccessListView, url_paccessix),
            ("detail", views.AccessDetailView, f"{url_paccessix}/<uuid:uuid>"),
            ("delete", views.AccessDeleteView, f"{url_paccessix}/<uuid:uuid>/delete"),
        ],
        kwargs,
    )


def _get_paths(model: type, basename: str, infos: list[tuple[str, type, str]], kwargs: dict[str, Any] | None = None):
    kwargs = kwargs or {}
    return [
        path(url, view.as_view(**{"model": model, **kwargs.get(kind, {})}), name=f"{basename}-{kind}")
        for kind, view, url in infos
    ]
