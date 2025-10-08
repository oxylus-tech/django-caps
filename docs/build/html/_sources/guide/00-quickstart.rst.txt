.. _quickstart:

Quickstart
==========

Add django-caps to installed apps and add middleware:


Setup
.....


In settings, add application and middleware. The middleware is used to assign user's :py:class:`~caps.models.agent.Agent` to the request.

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

    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "caps.backends.PermissionsBackend",
    ]


Create an object to be accessed:

.. code-block:: python

    # models.py
    from django.db import models
    from django.utils.translation import gettext_lazy as _

    from caps.models import Owned

    __all__ = ("Post",)


    # Create our example model. A Access and Capability model will be
    # generated and accessible from Post (Post.Access, Post.Capability)
    class Post(Owned):
        title = models.CharField(_("Title"), max_length=64)
        content = models.TextField(_("Content"))
        created_at = models.DateTimeField(_("Date of creation"), auto_now_add=True)

        # Allowed permissions with allowed reshare depth
        root_grants = {
            "app.view_post": 2, # can be shared then reshared
            "app.change_post": 1, # can be shared once
            "app.delete_post": 0, # can not be shared
        }


View and urls
.............

Using views provided by caps, example of ``urls.py`` file:

.. code-block:: python

    from django.urls import path

    from caps import views
    from . import models

    urlpatterns = [
        path("/post/", views.OwnedOwnedistView.as_view(model=models.Post), name="post-list"),
        path("/post/<uuid:uuid>/", views.OwnedOwnedetailView.as_view(model=models.Post), name="post-detail"),
        path("/post/create/", views.OwnedOwnedreateView.as_view(model=models.Post), name="post-create"),
        path(
            "/post/update/<uuid:uuid>",
            views.OwnedUpdateView.as_view(model=models.Post),
            name="post-update",
        ),
    ]

Even a shorter version, providing views for object accesses too:

.. code-block:: python

    from caps import urls
    from . import models

    # By settings `accesses=True` you also add default views for accesses assuming related templates exists (such as `myapp/postaccess_detail.html`).
    urlpatterns = urls.get_object_paths(models.Post, 'post', accesses=True)

You can have custom views as:

.. code-block:: python

    from caps import views
    from . import models, serializers

    __all__ = ("PostDetailView",)


    class PostDetailView(views.OwnedDetailView):
        model = models.Post

        # do something here...


Provided views
..............

Although we provide basic views for django-caps' models, we don't provide template, and it will be up to you to write them according Django practices.

We have views for the following models:

- :py:class:`~caps.models.agent.Agent`: :py:class:`~caps.views.common.AgentListView`, :py:class:`~caps.views.common.AgentDetailView`, :py:class:`~caps.views.common.AgentCreateView`, :py:class:`~caps.views.common.AgentUpdateView`, :py:class:`~caps.views.common.AgentDeleteView`;
- :py:class:`~caps.models.owned.Owned`: :py:class:`~caps.views.generics.OwnedListView`, :py:class:`~caps.views.generics.OwnedDetailView`, :py:class:`~caps.views.generics.OwnedCreateView`, :py:class:`~caps.views.generics.OwnedUpdateView`, :py:class:`~caps.views.generics.OwnedDeleteView`;

- :py:class:`~caps.models.access.Access`: :py:class:`~caps.views.common.AccessListView`, :py:class:`~caps.views.common.AccessDetailView`, :py:class:`~caps.views.common.AccessDeleteView`;

  We don't provide create and update views for access, as they should only be created when the object is created and by derivation (not provided yet). A Access should not be updated.


API
...

This is simple too, in ``viewsets.py``:

.. code-block:: python

    from caps import views
    from . import models, serializers

    __all__ = ('PostViewSet', 'PostAccessViewSet')

    # Example of viewset using DRF.
    # assuming you have implemented serializer for Post
    class PostViewSet(viewsets.OwnedViewSet):
        model = models.Post
        queryset = models.Post.objects.all()
        serializer_class = serializers.PostSerializer

    class PostAccessViewSet(viewsets.AccessViewSet):
        model = models.Post.Access
        queryset = models.Post.Access.objects.all()

Serializers:

.. code-block:: python

    from rest_framework import serializers
    from caps.serializers import OwnedSerializer

    from . import models

    __all__ = ('PostSerializer',)

    class PostSerializer(OwnedSerializer, serializers.ModelSerializer):
        class Meta:
            model = models.Post
            fields = OwnedSerializer.fields + ('title', 'content', 'created_at')

You'll have to manually add routes and urls for this part:

.. code-block:: python

    from django.urls import path
    from rest_framework.routers import SimpleRouter

    from . import viewsets

    router = SimpleRouter()
    router.register('post', viewsets.PostViewSet)
    router.register('post-access', viewsets.PostAccessViewSet)

    urlpatterns = [
        # ...
        path('api', include(router.urls)
    ]


Some example usage
..................

Example of Django-Caps' API usage:

.. code-block:: python

    from datetime import timedelta

    from django.contrib.auth.models import User, Permission
    from django.utils import timezone as tz

    from caps.models import Agent
    from .models import Post

    # We assume the users already exists
    user = User.objects.all()[0]
    user_1 = User.objects.all()[1]

    # Create agents (this is handled by middleware).
    agent = Agent.objects.create(user=user)
    agent_1 = Agent.objects.create(user=user_1)

    # Create the post
    post = Post.objects.create(owner=agent, title="Some title", content="Some content")

    # Share the post to agent 1 with default grants
    access = post.share(agent_1)
    assert access.grants == {"app.view_post": 1, "app.change_post": 0}

    # Or with an expiration datetime
    access = post.share(agent_1, expiration=tz.now() + timedelta(hours=2))

    # Lets imagine there is another agent called agent_2
    # Lets try to escalade privilege...
    access_2 = access.share(agent_2, {"app.view_post": 2, "app.change_post": 1})
    assert access_2.grants == {"app.view_post": 0}
