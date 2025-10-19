Django-Caps
===========

Django-Caps provides capability based object permission system for Django applications and Django Rest Framework.

This project is inspired by `Capn'Proto documentation <https://capnproto.org>`_ (`interesting paper <http://www.erights.org/elib/capability/ode/ode.pdf>`_).

A capability is a provided permission to a specific object. It can be *shared* a limited amount of time. Users never directly access the targeted object, but through a *access* that defines allowed capabilities for it.

In short, why use capabilities?

- *Granularity over objects permissions*
- *Reduced risk of privilege escalation*
- *Avoid direct access to database objects*
- `When to use capabilities (vs ACL)? <https://oxylus-tech.github.io/django-caps/build/html/guide/90-capability-vs-acl.html>`_

Documentation: https://oxylus-tech.github.io/django-caps/


Features
--------

Here is what we provide:

- **Capability based object permissions system**: objects can be shared with specific permissions to user/group. The object is then accessed by this shared object rather than directly (except for its owner).
- **Access sharing**: Objects' accesses can be shared with granular control on permissions.
- **Integration**: authentication/permission backend is provided both for Django and Django Rest Framework. Views, viewsets and serializers too.
- **Agents**: users can act under different profiles, as a user or group. The accesses always target other agents.

Among other things:

- **Database id obfuscation**: object internal id are never exposed to the outside world. Instead uuid are used to reference them in API and urls. This mitigate attacks on predictive id.



Short example
-------------

Lets create an object:

.. code-block:: python

    # models.py
    from django.db import models
    from django.utils.translation import gettext_lazy as _

    from caps.models import Owned

    __all__ = ("Post",)

    # Create our example model.
    class Post(Owned):
        title = models.CharField(_("Title"), max_length=64)
        content = models.TextField(_("Content"))
        # ... other fields

        # Allowed permissions with allowed reshare depth
        root_grants = {
            "app.view_post": 2, # can be shared then reshared
            "app.change_post": 1, # can be shared once
            "app.delete_post": 0, # can not be shared
        }


Small examples of Django-Caps' API usage:


.. code-block:: python

    from datetime import timedelta

    from django.contrib.auth.models import User, Permission
    from django.utils import timezone as tz

    from caps.models import Agent
    from .models import Post

    # User has 1-1 relation with an agent
    user = User.objects.all()[0]
    user_1 = User.objects.all()[1]

    # Create the post
    post = Post.objects.create(owner=user.agent, title="Some title", content="Some content")

    # Share the post to agent 1 with default grants
    access = post.share(user_1.agent)
    assert access.grants == {"app.view_post": 1, "app.change_post": 0}

    # Get objects for user_1
    objs = Post.objects.available(user_1.agent)


The views/viewsets will handle permission check depending on the action being requested.

For concrete usage, see the docs! 😉
