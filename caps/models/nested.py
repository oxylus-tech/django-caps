from typing import Any
from django.db import models

from caps.utils import nested


__all__ = ("NestedModelBase",)


class NestedModelBase(nested.NestedBase, models.base.ModelBase):
    """
    This metaclass allows to create nested model class based from parent one.

    See :py:class:`~caps.utils.nested.NestedBase` for more information about usage.
    """

    @classmethod
    def create_nested_class(cls, new_class: type[object], name: str, attrs: dict[str, Any] = {}) -> type:
        """
        Create the nested class for the provided container one to-be-created.

        It ensures the ``Meta`` class to have default values based on the new class (for app_label, abstract, etc.).
        """
        return super(NestedModelBase, cls).create_nested_class(
            new_class,
            name,
            {
                "Meta": cls.set_meta(
                    attrs,
                    defaults={
                        "__module__": new_class.__module__,
                        "app_label": new_class._meta.app_label,
                        "abstract": new_class._meta.abstract,
                        "proxy": new_class._meta.proxy,
                        "verbose_name": new_class._meta.verbose_name,
                        "verbose_name_plural": new_class._meta.verbose_name_plural,
                    },
                ),
                **attrs,
            },
        )

    @classmethod
    def set_meta(cls, attrs: dict[str, Any], set: dict[str, Any] = {}, defaults: dict[str, Any] = {}) -> type:
        """Get or create new meta class assigning to it the provided attributes.

        :param attrs: attribute to look into.
        :param set: attributes to set to the class.
        :param defaults: attributes to set to the class if not present.
        :return the Meta class.
        """
        meta = attrs.get("Meta") or type("Meta", tuple(), {})

        for k, v in set.items():
            setattr(meta, k, v)

        for k, v in defaults.items():
            not hasattr(meta, k) and setattr(meta, k, v)
        return meta
