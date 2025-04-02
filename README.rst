Django-Caps
===========

Django-Caps provides capability based object permission system for Django applications.
This project is inspired by `Capn'Proto documentation <https://capnproto.org>`
 (`interesting paper <http://www.erights.org/elib/capability/ode/ode.pdf>`).

A capability is a permission provided for a specific object. It can be *derived* (shared) a limited amount of time. Users never directly access the targeted object, but through a *reference* that defines allowed capabilities for it.

In short, why use capabilities?

- *Granularity over objects permissions*
- *Reduced risk of privilege escalation*
- *Avoid direct access to database objects*


Overview
--------

Features
........

This package provides:

- Capability based object permission system;
- Django permission backend, views and mixins;
- Django Rest Framework permissions, views, viewsets and serializers;
- A user can act under different profiles (agents);

Models
......

The current implementation provides the following models:

- ``Capability``: a single access right link to a specific action;
- ``Reference``: reference to an object, linked to an agent and a set of capabilities;
- ``Agent``: either an user or a group.

  Note: although capabilities are primarely designed to target only users, reducing ambient privilege (see below), we allow to assign them on groups. This allows to use capability-like system for object permissions on use-case not primarely targetted.

- ``Object``: objects to be accessed through references.


Quickstart
----------

Add django-caps to installed apps and add middleware:

.. code-block:: python

    # settings.py
    INSTALLED_APPS = [
        "caps"
        # add "caps.tests.apps" for development
        # ...
    ]

    MIDDLEWARE = [
        # we requires AuthenticationMiddleware as dependency
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "caps.middleware.AgentMiddleware",
        # ...
    ]


Create an object to be accessed:

.. code-block:: python

    # models.py
    from django.db import models
    from django.utils.translation import gettext_lazy as _

    from caps.models import Object

    class Post(Object):
        title = models.CharField(_("Title"), max_length=64)
        content = models.TextField(_("Content"))
        created_at = models.DateTimeField(_("Date of creation"), auto_now_add=True)

Basic example usage:

.. code-block:: python

    from django.contrib.auth.models import User

    from caps.models import Agent
    from .models import Post

    # We assume the users already exists
    user = User.objects.all()[0]
    user_1 = User.objects.all()[1]

    # Create agents (this is handled by middleware).
    agent = Agent.objects.create(user=user)
    agent_1 = Agent.objects.create(user=user)

    # Create capabilities
    capabilities = [
        # Capability can be re-shared 10 times.
        Capability(name="read", max_derive=10),
        # These ones can not be shared
        Capability(name="write"),
        Capability(name="update"),
    ]
    # Capabilities are only created once per `name` and `max_derive`.
    # This method is provided by django-caps.
    Capability.objects.get_or_create_many(capabilities)

    # Create the post
    post = Post.objects.create(title="Some title", content="Some content")
    ref = Post.Reference.create(agent, object, capabilities)

    # Get the object
    the_post = Post.objects.ref(agent, ref.uuid)

    # This raises a DoesNotExist error
    Post.objects.ref(agent_1, ref.uuid)

    # This create a new reference with only shareable capabilities
    ref_1 = ref.derive(agent_1, capabilities)


Capability vs ACL permission systems
------------------------------------

#. Granular and Delegable Access Control

    - In a capability-based system, access rights are directly assigned to objects (capabilities) rather than being centrally managed per resource.
    - Advantage: Users can delegate access rights without requiring modifications to a central policy (e.g., passing a token or capability reference to another user).
    - In contrast: ACLs require explicit permission modifications on the resource, which can be complex and require admin intervention.

#. Reduced Need for a Central Authority

    - Capabilities are typically self-contained (e.g., a token, key, or reference) and grant access upon presentation.
    - Advantage: There is no need for continuous lookups in a central access control database.
    - In contrast: ACL-based systems require checking a central list for each access attempt, which can create performance bottlenecks.

#. Better Security Against Privilege Escalation

    - Capabilities are unforgeable and granted explicitly to users or processes.
    - Advantage: It prevents confused deputy attacks (where a process inadvertently misuses privileges granted by another entity).
    - In contrast: ACLs check permissions based on identity, which can lead to privilege escalation through indirect means (e.g., exploiting a process with broad access).

#. More Dynamic and Scalable Access Control

    - Capability-based models are inherently distributed and flexible.
    - Advantage: New permissions can be granted dynamically without modifying a central ACL.
    - In contrast: ACLs require centralized policy updates and administrative overhead.

#. Easier Revocation and Least Privilege Enforcement

    - Capability-based models can revoke access by simply invalidating or expiring the capability.
    - Advantage: Fine-grained control over individual access rights.
    - In contrast: ACLs may require searching for all instances of a user’s permissions and modifying multiple entries.

#. Better Fit for Decentralized or Distributed Systems

    - Many modern cloud, containerized, and microservices architectures favor capabilities (e.g., bearer tokens, OAuth, API keys).
    - Advantage: Eliminates reliance on a single access control authority, improving resilience.
    - In contrast: ACLs are often tied to a centralized authentication and authorization model.

So... When to use what?

    - Capability-based systems are ideal for distributed, decentralized, and microservices-based environments, where flexibility, delegation, and security are key.
    - ACL-based systems are better suited for traditional enterprise IT environments, where strict identity-based access control is needed.

    This however still can be usable for object permissions by providing references for groups instead of users.
