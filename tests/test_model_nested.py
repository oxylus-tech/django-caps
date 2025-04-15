# TODO: Theses tests caps.utils.nested in the same row => split the tests.
import pytest

from django.db import models
from caps.models import nested
from caps.models.capability_set import CapabilitySet


class ParentBase(nested.NestedBase):
    nested_name = "Caps"
    nested_class = CapabilitySet

    @classmethod
    def create_nested_class(cls, new_class, name, attrs={}):
        return super(ParentBase, cls).create_nested_class(new_class, name, {**attrs, "from_create_nested_class": 234})


class InvalidBase(nested.NestedBase):
    pass


class Parent(models.Model, metaclass=ParentBase):
    class Meta:
        app_label = "tests.app"


class Parent2(Parent):
    class Caps(CapabilitySet):
        pass

    DeclaredNested = Caps

    class Meta:
        app_label = "tests.app"


class TestNestedBase:
    def test___new__(cls):
        assert issubclass(Parent.Caps, CapabilitySet)
        assert Parent.Caps.__module__ == Parent.__module__

    def test_get_nested_class_is_declared(cls):
        assert Parent2.Caps is Parent2.DeclaredNested

    def test_get_nested_class_is_not_declared(cls):
        assert issubclass(Parent.Caps, ParentBase.nested_class)
        assert Parent.Caps is not ParentBase.nested_class

    def test_get_nested_class_raises_missing_nested_class_attr(cls):
        with pytest.raises(ValueError):
            InvalidBase.get_nested_class(Parent)

    def test_get_nested_class_not_subclass(cls):
        with pytest.raises(ValueError):

            class Invalid(ParentBase):
                nested_class = TestNestedBase

            class Child(models.Model, metaclass=Invalid):
                class Caps:
                    pass

                class Meta:
                    app_label = "tests.app"

    def test_create_nested_class(cls):
        assert getattr(Parent.Caps, "from_create_nested_class")
