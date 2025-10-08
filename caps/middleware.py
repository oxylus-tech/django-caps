from django.http import HttpRequest

from .models import Agent, AgentQuerySet

__all__ = ("AgentMiddleware",)


class AgentMiddleware:
    """
    This middleware adds user's agents to the request object, as:

        - ``agent``: the current agent user is acting as;
        - ``agents``: the agents user can impersonate.

    It creates user's default agent if none is already present.

    You can add it to the ``MIDDLEWARE`` setting, after ``AuthenticationMiddleware``:

    ..code-block:: python

        MIDDLEWARE = [
            # ...
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            # ...
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            "caps.middleware.AgentMiddleware",
        ]

    """

    agent_class = Agent
    """Agent model class to use."""
    agent_cookie_key = "django_caps.agent"
    """Cookie used to get agent."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        request.agents = self.get_agents(request)
        request.agent = self.get_agent(request, request.agents)
        return self.get_response(request)

    def get_agents(self, request: HttpRequest) -> AgentQuerySet:
        """Return queryset for user's agents, ordered by ``-user_id``."""
        return Agent.objects.user(request.user, strict=False).order_by("-user_id")

    def get_agent(self, request: HttpRequest, agents: AgentQuerySet) -> Agent:
        """Return user's active agent."""
        if request.user.is_anonymous:
            return next(iter(agents), None)
        if agent := getattr(request.user, "agent", None):
            return agent

        agent = Agent.objects.create(user=request.user)
        # assign agent to request's user as it ain't already present
        request.user.__dict__["agent"] = agent
        return agent
