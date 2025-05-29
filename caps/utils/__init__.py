from typing import Any


def get_lazy_relation(obj, field, out_field: str | None = None) -> tuple[str, Any]:
    """
    For the provided model instance, return an attribute name and value for field.

    It returns relation id if the relation hasn't been fetched from the db. Otherwise, it returns the relation object:

    .. code-block:: python

        access = Access.objects.all().first()

        # relation has not been fetched
        k, v = get_lazy_relation(access, 'origin')
        assert k == 'origin_id' and isinstance(v, int)

        # fetch from db:
        access.origin
        k, v = get_lazy_relation(access, 'origin')
        assert k == 'origin' and isinstance(v, Access)

        # map a name:
        k, v = get_lazy_relation(access, 'origin', 'dest')
        assert k == 'dest' and isinstance(v, Access)

    :param obj: object to get value on
    :param field: object's field to lookup
    :param out_field: output field (default to object's)

    :return a tuple with field name and value.

    """
    out_field = out_field or field
    if field in obj.__dict__:
        return out_field, getattr(obj, field)
    return f"{out_field}_id", getattr(obj, f"{field}_id", None)
