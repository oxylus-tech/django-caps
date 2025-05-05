import pytest


from .conftest import req_factory, init_request
from caps.views import generics


@pytest.fixture
def create_view(user_agent, user_agents):
    req = req_factory.post("/test", {"name": "name"})
    req = init_request(req, user_agent, user_agents)
    return generics.ObjectCreateView(request=req)


@pytest.mark.django_db(transaction=True)
class TestObjectCreateView:
    pass
    # TODO
    # def test_form_valid(self, create_view):
    #    pass
