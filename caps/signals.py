from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group

from .models import Agent


@receiver(post_save, sender=User)
def create_user_agent(sender, instance, created, *args, **kwargs):
    """Ensure agent is created for each user being saved."""
    if not hasattr(instance, "agent"):
        Agent.objects.create(user=instance)


@receiver(post_save, sender=Group)
def create_group_agent(sender, instance, created, *args, **kwargs):
    """Ensure agent is created for each group being saved."""
    if not hasattr(instance, "agent"):
        Agent.objects.create(group=instance)
