from django.http import HttpRequest

from .models import Agent, AgentQuerySet

__all__ = ("AgentMiddleware",)


class AgentMiddleware:
    """
    This middleware adds user's agents to the request object, as:

        - `agent`: the current agent user is acting as;
        - `agents`: the agents user can impersonate.

    It creates user's default agent if there are none already present.
    """

    """Fetch request user's active agent, and assign it to
    ``request.agent``."""

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
        """Return queryset for user's agents, ordered by ``-is_default``."""
        return Agent.objects.user(request.user, strict=False).order_by("-is_default")

    def get_agent(self, request: HttpRequest, agents: AgentQuerySet) -> Agent:
        """Return user's active agent."""
        cookie = request.COOKIES.get(self.agent_cookie_key)
        if cookie:
            # we iterate over agents instead of fetching extra queryset
            # this keeps cache for further operations.
            agent = next((r for r in agents if r.uuid == cookie), None)
            if agent:
                return agent

        if request.user.is_anonymous:
            return next(iter(agents), None)

        # agents are sorted such as default are first:
        # predicates order ensure that we return first on is_default
        # then only if is user
        it = (r for r in agents if r.is_default or r.user_id == request.user.id)
        if agent := next(it, None):
            return agent

        return Agent.objects.create(user=request.user, is_default=True)
