from typing import Any

from django.urls import path

from . import models, views


def get_object_paths(
    obj_class: type[models.Object],
    url_prefix: str | None = None,
    kwargs: dict[str, Any] | None = None,
    basename: str = "",
    references: bool = False,
    ref_kwargs: dict[str, Any] | None = None,
) -> list[path]:
    """
    Return Django paths for the provided object class, including to edit reference (:py:func:`get_reference_path`).

    .. code-block:: python

        from caps.urls import get_object_paths
        from . import models

        urlpatterns = (
            get_object_paths(models.Post, 'post')
        )

    :param obj_class: the object model class;
    :param url_prefix: url base path (default to model name);
    :param kwargs: ``as_view`` kwargs, by view kind (list, detail, etc.)
    :param basename: use this as url's basename (default to model name)
    :param references: if True, generate path for Object's Reference using default view (see :py:mod:`caps.views.common`)
    :param ref_kwargs: ``kwargs`` argument passed down to :py:func:`get_reference_class`.

    :return: a list of path
    """
    if not basename:
        basename = obj_class._meta.model_name
    if url_prefix is None:
        url_prefix = basename
    kwargs = kwargs or {}
    return _get_paths(
        obj_class,
        basename,
        [
            ("list", views.ObjectListView, url_prefix),
            ("detail", views.ObjectDetailView, f"{url_prefix}/<uuid:uuid>"),
            ("create", views.ObjectCreateView, f"{url_prefix}/create"),
            ("update", views.ObjectUpdateView, f"{url_prefix}/<uuid:uuid>/update"),
            ("delete", views.ObjectDeleteView, f"{url_prefix}/<uuid:uuid>/delete"),
        ],
        kwargs,
    ) + get_reference_paths(obj_class.Reference, f"{url_prefix}/reference", kwargs=ref_kwargs)


def get_reference_paths(
    ref_class: type[models.Reference],
    url_prefix: str = "reference",
    kwargs: dict[str, Any] | None = None,
    basename: str = "",
) -> list[path]:
    """
    Return Django paths for the provided reference class.

    Created path for views: ``list``, ``detail``, ``delete``.

    The path will have names such as (for a model named ``contact``): ``contact-reference-list``.

    :param ref_class: Reference class
    :param kwargs: ``as_view`` extra arguments by view type
    :param basename: use this a base name for url, instead of ``{object_model_name}-reference``.
    :returns: list of path
    """
    if not basename:
        obj_class = ref_class.get_object_class()
        basename = f"{obj_class._meta.model_name}-reference"
    return _get_paths(
        ref_class,
        basename,
        [
            ("list", views.ReferenceListView, url_prefix),
            ("detail", views.ReferenceDetailView, f"{url_prefix}/<uuid:uuid>"),
            ("delete", views.ReferenceDeleteView, f"{url_prefix}/<uuid:uuid>/delete"),
        ],
        kwargs,
    )


def _get_paths(model: type, basename: str, infos: list[tuple[str, type, str]], kwargs: dict[str, Any] | None = None):
    kwargs = kwargs or {}
    return [
        path(url, view.as_view(**{"name": f"{basename}-{kind}", "model": model, **kwargs.get(kind, {})}))
        for kind, view, url in infos
    ]
