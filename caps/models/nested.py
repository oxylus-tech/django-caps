from typing import Any
from django.db import models


class NestedBase(models.base.ModelBase):
    """
    This metaclass allows to create nested model class based from parent one.

    By default, the method will first look for an existing declaration.
    If none is found it will create one with only the declared :py:attr:`nested_class` as base. This means that you must manually declare any other parent class:

    .. code-block:: python

        class Nested:
            pass

        class ParentBase(NestedBase):
            nested_class = Nested

            @classmethod
            def create_nested_class(cls, name, attrs={}):
                return super(Parent, cls).create_nested_class(
                    name,
                    {"custom_field": ForeignKey()}
                )

        class Parent(metaclass=NestedBase):
            pass

        class A(Parent):
            # you must declare its bases
            class Nested(Nested):
                # customize code here
                pass

        class C(A, B):
            # you need to be explicit
            class Nested(A.Nested):
                pass
    """

    nested_class: type[object] = None
    """ Nested class base to create. """
    nested_name: str | None = None
    """ Attribute and class name of the nested class. If not provided, takes it from :py:attr:`nested_class` """
    new_name: str = "{class_name}{nested_name}"
    """ Name format for newly created classes. """

    def __new__(cls, name, bases, attrs):
        new_class = super(NestedBase, cls).__new__(cls, name, bases, attrs)
        nested_class = cls.get_nested_class(new_class)
        setattr(new_class, cls.nested_name, nested_class)
        return new_class

    @classmethod
    def get_nested_class(cls, new_class: type[object]):
        """Get nested model class or creates a new one."""
        if not cls.nested_class:
            raise ValueError(f"Missing attribute `nested_class` on {cls}.")
        if not cls.nested_name:
            cls.nested_name = cls.nested_class.__name__

        nested_name, nested_class = cls.nested_name, cls.nested_class
        declared = new_class.__dict__.get(nested_name)

        if not declared:
            return cls.create_nested_class(
                new_class,
                cls.new_name.format(class_name=new_class.__name__, nested_name=nested_name),
                {"__module__": new_class.__module__},
            )
        elif not issubclass(declared, nested_class):
            raise ValueError(f"`{nested_name}` member of `{new_class.__name__}` must be a subclass of `{declared}`")
        return declared

    @classmethod
    def create_nested_class(cls, new_class: type[object], name: str, attrs: dict[str, Any] = {}) -> type:
        """
        Create the nested class for the provided container one to-be-created.

        :param new_class: the parent class that just has been created
        :param name: nested class name
        :param attrs: nested class attributes
        :return the newly created class.
        """
        meta_class = cls.nested_class.__class__
        attrs["Meta"] = cls.set_meta(
            attrs,
            defaults={
                "__module__": new_class.__module__,
                "app_label": new_class._meta.app_label,
                "abstract": new_class._meta.abstract,
                "proxy": new_class._meta.proxy,
            },
        )
        return meta_class.__new__(meta_class, name, (cls.nested_class,), attrs)

    @classmethod
    def set_meta(cls, attrs: dict[str, Any], set: dict[str, Any] = {}, defaults: dict[str, Any] = {}) -> type:
        """Get or create new meta class assigning to it the provided attributes.

        :param attrs: attribute to look into
        :param set: attributes to set to the class
        :param defaults: attributes to set to the class if not present
        :return the Meta class.
        """
        meta = attrs.get("Meta") or type("Meta", tuple(), {})

        for k, v in set.items():
            setattr(meta, k, v)

        for k, v in defaults.items():
            not hasattr(meta, k) and setattr(meta, k, v)
        return meta
