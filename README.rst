Django-Caps
===========

Django-Caps provides capability based object permission system for Django applications.
This project is inspired by `Capn'Proto documentation <https://capnproto.org>`_ (`interesting paper <http://www.erights.org/elib/capability/ode/ode.pdf>`_).

A capability is a permission provided for a specific object. It can be *derived* (shared) a limited amount of time. Users never directly access the targeted object, but through a *reference* that defines allowed capabilities for it.

In short, why use capabilities?

- *Granularity over objects permissions*
- *Reduced risk of privilege escalation*
- *Avoid direct access to database objects*

More in the guide, :ref:`Capability vs ACL permission systems`.


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

    __all__ = ("Post",)


    # Create our example model. A Reference and Capability model will be
    # generated and accessible from Post (Post.Reference, Post.Capability)
    class Post(Object):
        title = models.CharField(_("Title"), max_length=64)
        content = models.TextField(_("Content"))
        created_at = models.DateTimeField(_("Date of creation"), auto_now_add=True)

Using views provided by caps, example of ``urls.py`` file:

.. code-block:: python

    from django.urls import path

    from caps import views
    from . import models

    urlpatterns = [
        path("/post/", views.ObjectListView.as_view(model=models.Post), name="post-list"),
        path("/post/<uuid:uuid>/", views.ObjectDetailView.as_view(model=models.Post), name="post-detail"),
        path("/post/create/", views.ObjectCreateView.as_view(model=models.Post), name="post-create"),
        path(
            "/post/update/<uuid:uuid>",
            views.ObjectUpdateView.as_view(model=models.Post),
            name="post-update",
        ),
    ]

You can have custom views as:

.. code-block:: python

    from caps import views, viewsets
    from . import models, serializers

    __all__ = ("PostDetailView", "PostViewSet")


    class PostDetailView(views.ObjectListView):
        model = models.Post

    # Example of viewset using DRF.
    # assuming you have implemented serializer for Post
    class PostViewSet(viewsets.ObjectViewSet):
        model = models.Post
        queryset = models.Post.objects.all()
        serializer_class = serializers.PostSerializer


Example of Django-Caps' API usage:

.. code-block:: python

    from django.contrib.auth.models import User, Permission

    from caps.models import Agent
    from .models import Post

    # We assume the users already exists
    user = User.objects.all()[0]
    user_1 = User.objects.all()[1]

    # Create agents (this is handled by middleware).
    agent = Agent.objects.create(user=user)
    agent_1 = Agent.objects.create(user=user_1)

    # Create allowed capabilities for Post
    # Theses will be used as default ones for Post's root Reference
    permissions = Permission.objects.all()[:3]
    capabilities = [Post.Capability(permission=perm, max_derive=2) for perm in Permission]

    Post.Capability.objects.bulk_create(capabilities)

    # Create the post and the root reference
    # Root reference: the original reference from which all other references
    # are derived (created/shared).
    post = Post.objects.create(title="Some title", content="Some content")
    ref = Post.Reference.create_root(agent, object)

    # Get the object
    the_post = Post.objects.refs(ref).first()

    # This create a new reference with only shareable capabilities (max_derive>0)
    ref_1 = ref.derive(agent_1, capabilities)
