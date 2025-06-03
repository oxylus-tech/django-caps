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


def test_api_create_access(client, client_2, user_2, group_agent):
    resp = client.post(reverse("concreteowned-list"), {"name": "Name"})
    assert resp.data["id"]

    # Test other don't have access
    uuid = resp.data["id"]
    resp = client_2.get(reverse("concreteowned-detail", args=[uuid]))
    assert resp.status_code in (403, 404)

    # Test other don't have right to create
    resp = client_2.post(reverse("concreteowned-list"), {"name": "Name 22"})
    assert resp.status_code == 403

    # Test update (granted)
    resp = client.put(reverse("concreteowned-detail", args=[uuid]), {"name": "Name 23"})
    assert resp.status_code == 200

    # Share
    resp = client.post(
        reverse("concreteowned-share", args=[uuid]),
        {"receiver": user_2.agent.uuid, "grants": {"caps_test.view_concreteowned": 0}},
        format="json",
    )
    assert resp.status_code == 201

    access_uuid = resp.data["id"]

    # Access by object uuid not allowed for user 2
    resp = client_2.get(reverse("concreteowned-detail", args=[uuid]))
    assert resp.status_code == 404

    # Only by shared access
    resp = client_2.get(reverse("concreteowned-detail", args=[access_uuid]))
    assert resp.status_code == 200
    assert resp.data["id"] == access_uuid

    # default ConcreteOwned don't grant deletion
    resp = client_2.delete(reverse("concreteowned-detail", args=[access_uuid]))
    assert resp.status_code == 403

    # Share from object forbidden on user 2
    resp = client_2.post(reverse("concreteowned-share", args=[access_uuid]), {"receiver": user_2.agent.uuid})
    assert resp.status_code == 403

    # Derive should not happen here
    resp = client_2.post(
        reverse("concreteownedaccess-share", args=[access_uuid]),
        {"receiver": group_agent.uuid},
    )
    assert resp.status_code == 403
