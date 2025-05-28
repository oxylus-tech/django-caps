import pytest

from rest_framework.test import APIClient
from django.test import Client
from django.urls import reverse


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def client(user, user_perms):
    client = APIClient()
    client.force_login(user)
    return client


@pytest.fixture
def client_2(user_2, user_2_perms):
    client = Client()
    client.force_login(user_2)
    return client


def test_api_create_reference(client, client_2, user_2, group_agent):
    resp = client.post(reverse("concreteobject-list"), {"name": "Name"})
    assert resp.data["uuid"]

    # Test other don't have access
    uuid = resp.data["uuid"]
    resp = client_2.get(reverse("concreteobject-detail", args=[uuid]))
    assert resp.status_code in (403, 404)

    # Test other don't have right to create
    resp = client_2.post(reverse("concreteobject-list"), {"name": "Name 22"})
    assert resp.status_code == 403

    # Test update (granted)
    resp = client.put(reverse("concreteobject-detail", args=[uuid]), {"name": "Name 23"})
    assert resp.status_code == 200

    # Share
    resp = client.post(
        reverse("concreteobject-share", args=[uuid]),
        {"receiver": user_2.agents.all().first().uuid, "grants": {"caps_test.view_concreteobject": 0}},
        format="json",
    )
    assert resp.status_code == 200

    # Ensure access
    resp = client_2.get(reverse("concreteobject-detail", args=[uuid]))
    assert resp.status_code == 200
    ref_uuid = resp.data["reference"]["uuid"]

    # default ConcreteObject don't grant deletion
    resp = client_2.delete(reverse("concreteobject-detail", args=[uuid]))
    assert resp.status_code == 403

    # Share from object forbidden on user 2
    resp = client_2.post(reverse("concreteobject-share", args=[uuid]), {"receiver": user_2.agents.all().first().uuid})
    assert resp.status_code == 403

    # Derive should not happen here
    resp = client_2.post(
        reverse("concreteobjectreference-share", args=[ref_uuid]),
        {"receiver": group_agent.uuid},
    )
    assert resp.status_code == 403
