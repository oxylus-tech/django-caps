import pytest


from .conftest import req_factory, init_request
from caps.views import generics


@pytest.fixture
def create_view(user, user_agents):
    req = init_request(req_factory.post("/test", {"name": "name"}), user)
    return generics.OwnedCreateView(request=req)


@pytest.mark.django_db(transaction=True)
class TestOwnedCreateView:
    pass
    # TODO
    # def test_form_valid(self, create_view):
    #    pass
