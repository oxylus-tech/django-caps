from datetime import timedelta
import pytest

from django.utils import timezone as tz

from .app.models import ConcreteObject, Reference
from .conftest import assertCountEqual


class TestObjectQuerySet:
    def test_available_with_owner(self, user_agent, objects, user_2_object):
        query = ConcreteObject.objects.available(user_agent)
        assertCountEqual(query, objects)

    def test_available_with_reference(self, user_2_agent, objects):
        objects[0].share(user_2_agent)
        query = ConcreteObject.objects.available(user_2_agent)
        assert list(query) == [objects[0]]

    def test_available_with_reference_expired(self, user_2_agent, objects):
        objects[0].share(user_2_agent, expiration=tz.now() - timedelta(hours=1))
        assert not ConcreteObject.objects.available(user_2_agent).exists()

    def test_refs(self, agents, refs):
        for agent in agents:
            query = Reference.objects.receiver(agent)
            q_uuids = list(query.values_list("uuid", flat=True))
            result = ConcreteObject.objects.refs(query, strict=True)
            uuids = [r.reference.uuid for r in result]
            assertCountEqual(uuids, q_uuids)


@pytest.mark.django_db(transaction=True)
class TestObject:
    def test_check_root_grants(self):
        ConcreteObject.check_root_grants()

    def test_check_root_grants_raises_value_error(self):
        class SubClass(ConcreteObject):
            root_grants = {"invalid-permission": 1}

            class Meta:
                app_label = "caps_test"

        with pytest.raises(ValueError):
            SubClass.check_root_grants()

    def test_share_with_default_grants(self, user_2_agent, object):
        ref = object.share(user_2_agent)
        assert ref.grants and ref.grants == object.root_grants

    def test_share_with_grants(self, user_2_agent, object):
        # we force upper and extra value, it should be set to allowed one
        grants = {k: v + 1 for k, v in object.root_grants.items()}
        grants["extra_perm"] = 123

        ref = object.share(user_2_agent)
        assert ref.grants and ref.grants == object.root_grants

    def test_get_absolute_url(self, object, ref):
        assert object.get_absolute_url()
