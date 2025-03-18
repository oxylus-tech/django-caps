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

    A user can impersonate multiple agent.
    """

    ref = models.UUIDField(_("Reference"), default=uuid.uuid4)
    """Public reference to agent."""
    user = models.ForeignKey(User, models.CASCADE, null=True, blank=True, verbose_name=_("User"))
    """Agent targets this user."""
    group = models.ForeignKey(Group, models.CASCADE, null=True, blank=True, verbose_name=_("Group"))
    """Agent targets this group."""
    is_default = models.BooleanField(_("Default User Agent"), default=False, blank=True)
    """If True, use this Agent as user's default."""

    objects = AgentQuerySet.as_manager()

    @property
    def is_anonymous(self) -> bool:
        """Return True when Agent targets anonymous users."""
        return not self.user and not self.group

    def clean(self):
        if self.user and self.group:
            raise ValidationError(_("Agent targets either a user or a group"))
        if self.is_default and not (self.user or self.is_anonymous):
            raise ValidationError(_("Agent can be set as default only when targeting a user."))
        super().clean()
