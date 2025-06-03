from datetime import timedelta
import pytest

from django.utils import timezone as tz

from .app.models import ConcreteOwned, Access
from .conftest import assertCountEqual


class TestOwnedQuerySet:
    def test_available_with_owner(self, user_agent, objects, user_2_object):
        query = ConcreteOwned.objects.available(user_agent)
        assertCountEqual(query, objects)

    def test_available_with_access(self, user_2_agent, objects):
        objects[0].share(user_2_agent)
        query = ConcreteOwned.objects.available(user_2_agent, Access.objects.all())
        assert list(query) == [objects[0]]

    def test_available_with_access_expired(self, user_2_agent, objects):
        objects[0].share(user_2_agent, expiration=tz.now() - timedelta(hours=1))
        assert not ConcreteOwned.objects.available(user_2_agent, Access.objects.all()).exists()

    def test_access(self, agents, accesses):
        for agent in agents:
            query = Access.objects.receiver(agent)
            q_uuids = list(query.values_list("uuid", flat=True))
            result = ConcreteOwned.objects.access(query, strict=True)
            uuids = [r.access.uuid for r in result]
            assertCountEqual(uuids, q_uuids)


@pytest.mark.django_db(transaction=True)
class TestOwned:
    def test_check_root_grants(self):
        ConcreteOwned.check_root_grants()

    def test_check_root_grants_raises_value_error(self):
        class SubClass(ConcreteOwned):
            root_grants = {"invalid-permission": 1}

            class Meta:
                app_label = "caps_test"

        with pytest.raises(ValueError):
            SubClass.check_root_grants()

    def test_share_with_default_grants(self, user_2_agent, object):
        access = object.share(user_2_agent)
        assert access.grants and access.grants == object.root_grants

    def test_share_with_grants(self, user_2_agent, object):
        # we force upper and extra value, it should be set to allowed one
        grants = {k: v + 1 for k, v in object.root_grants.items()}
        grants["extra_perm"] = 123

        access = object.share(user_2_agent)
        assert access.grants and access.grants == object.root_grants

    def test_get_absolute_url(self, object, access):
        assert object.get_absolute_url()
