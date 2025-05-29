from __future__ import annotations

import uuid

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

__all__ = ("AgentQuerySet", "Agent")


class AgentQuerySet(models.QuerySet):
    def create_for_users(self, users: models.QuerySet[User] | None) -> AgentQuerySet:
        """Create Agent for all users that don't have one assigned yet.

        :param users: if provided only for those users
        :return: newly created agent (excluding existing ones)
        """
        if users is None:
            users = User.objects.all()

        db = set(users.filter(agent__is_default=True).values_list("id", flat=True))
        return self.model.bulk_create(self.model(user=user, is_default=True) for user in users if user.id not in db)

    def create_for_groups(self, groups: models.QuerySet[Group] | None) -> AgentQuerySet:
        """Create Agent for all users that don't have one assigned yet.

        :param users: if provided only for those users
        :return: newly created agent (excluding existing ones)
        """
        if groups is None:
            groups = Group.objects.all()

        db = set(groups.filter(agent__isnull=False).values_list("id", flat=True))
        return self.model.bulk_create(self.model(group=group) for group in groups if group.id not in db)

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

    uuid = models.UUIDField(_("Access"), default=uuid.uuid4)
    """Public access to agent."""
    user = models.ForeignKey(User, models.CASCADE, null=True, blank=True, related_name="agents")
    """Agent targets this user. Related name: 'agents'. """
    group = models.ForeignKey(Group, models.CASCADE, null=True, blank=True, related_name="agents")
    """Agent targets this group. Related name: 'agents'. """
    is_default = models.BooleanField(_("Default User Agent"), default=False, blank=True)
    """If True, use this Agent as user's default."""

    objects = AgentQuerySet.as_manager()

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
        if self.is_default and not (self.user or self.is_anonymous):
            raise ValidationError(_("Agent can be set as default only when targeting a user."))
        super().clean()
