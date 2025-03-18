django-caps
===========

django-caps provides capability based permission system for django applications. This project is inspired by [Capn'Proto documentation](https://capnproto.org)
 ([interesting paper](http://www.erights.org/elib/capability/ode/ode.pdf)).

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

Add django-caps to installed apps and add middleware

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
