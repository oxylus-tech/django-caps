from __future__ import annotations

import uuid

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

__all__ = ("AgentQuerySet", "Agent")


class AgentQuerySet(models.QuerySet):
    def user(self, user: User, strict: bool = False) -> AgentQuerySet:
        """Filter by user or its groups.

        :param user: User
        :param strict: if False, search on user's groups.
        """
        if user.is_anonymous:
            return self.filter(user__isnull=True, group__isnull=True)
        if strict:
            return self.filter(user=user)
        return self.filter(Q(user=user) | Q(group__in=user.groups.all())).distinct()

    def group(self, group: Group) -> AgentQuerySet:
        """Filter by group."""
        return self.filter(group=group)


class Agent(models.Model):
    """
    An agent is the one executing an action. It can either be related to
    a specific user (anonymous included) or group.
    """

    uuid = models.UUIDField(_("Access"), default=uuid.uuid4)
    """Public access to agent."""
    user = models.OneToOneField(User, models.CASCADE, null=True, blank=True)
    """Agent targets this user. Related name: 'agents'. """
    group = models.OneToOneField(Group, models.CASCADE, null=True, blank=True)
    """Agent targets this group. Related name: 'agents'. """

    objects = AgentQuerySet.as_manager()

    class Meta:
        verbose_name = _("Agent")
        verbose_name_plural = _("Agents")

    @property
    def is_anonymous(self) -> bool:
        """Return True when Agent targets anonymous users."""
        return not self.user and not self.group

    def is_agent(self, user: User):
        """Return True if user can act as this agent.

        This methods also check based on user's group and anonymity.
        """
        if user.is_anonymous:
            return self.is_anonymous
        return self.user_id == user.pk or any(
            gid == self.group_id for gid in user.groups.all().values_list("pk", flat=True)
        )

    def clean(self):
        if self.user and self.group:
            raise ValidationError(_("Agent targets either a user or a group"))
        super().clean()

    def __str__(self):
        if self.user:
            return f"User '{self.user.username}'"
        if self.group:
            return f"Group '{self.group.name}'"
        return "Anonymous"
