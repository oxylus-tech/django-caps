Quickstart
==========

Add django-caps to installed apps and add middleware:


Setup
.....

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


View and urls
.............

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

Even a shorter version, providing views for object references too:

.. code-block:: python

    from caps import urls
    from . import models

    # By settings `references=True` you also add default views for references assuming related templates exists (such as `myapp/postreference_detail.html`).
    urlpatterns = urls.get_object_paths(models.Post, 'post', references=True)

You can have custom views as:

.. code-block:: python

    from caps import views, viewsets
    from . import models, serializers

    __all__ = ("PostDetailView", "PostViewSet")


    class PostDetailView(views.ObjectDetailView):
        model = models.Post

        # do something here...


Provided views
..............

Although we provide basic views for django-caps' models, we don't provide template, and it will be up to you to write them according Django practices.

We have views for the following models:

- :py:class:`~caps.models.agent.Agent`: :py:class:`~caps.views.common.AgentListView`, :py:class:`~caps.views.common.AgentDetailView`, :py:class:`~caps.views.common.AgentCreateView`, :py:class:`~caps.views.common.AgentUpdateView`, :py:class:`~caps.views.common.AgentDeleteView`; -
- :py:class:`~caps.models.object.Object`: :py:class:`~caps.views.generics.ObjectListView`, :py:class:`~caps.views.generics.ObjectDetailView`, :py:class:`~caps.views.generics.ObjectCreateView`, :py:class:`~caps.views.generics.ObjectUpdateView`, :py:class:`~caps.views.generics.ObjectDeleteView`;

- :py:class:`~caps.models.reference.Reference`: :py:class:`~caps.views.common.ReferenceListView`, :py:class:`~caps.views.common.ReferenceDetailView`, :py:class:`~caps.views.common.ReferenceDeleteView`;

  We don't provide create and update views for reference, as they should only be created when the object is created and by derivation (not provided yet). A Reference should not be updated.


API
...

This is simple too, in ``viewsets.py``:

.. code-block:: python

    from caps import views
    from . import models, serializers

    __all__ = ('PostViewSet', 'PostReferenceViewSet')

    # Example of viewset using DRF.
    # assuming you have implemented serializer for Post
    class PostViewSet(viewsets.ObjectViewSet):
        model = models.Post
        queryset = models.Post.objects.all()
        serializer_class = serializers.PostSerializer

    class PostReferenceViewSet(viewsets.ReferenceViewSet):
        model = models.Post.Reference
        queryset = models.Post.Reference.objects.all()

Serializers:

.. code-block:: python

    from rest_framework import serializers
    from caps.serializers import ObjectSerializer

    from . import models

    __all__ = ('PostSerializer',)

    class PostSerializer(ObjectSerializer, serializers.ModelSerializer):
        class Meta:
            model = models.Post
            fields = ObjectSerializer.fields + ('title', 'content', 'created_at')

You'll have to manually add routes and urls for this part:

.. code-block:: python

    from django.urls import path
    from rest_framework.routers import SimpleRouter

    from . import viewsets

    router = SimpleRouter()
    router.register('post', viewsets.PostViewSet)
    router.register('post-reference', viewsets.PostReferenceViewSet)

    urlpatterns = [
        # ...
        path('api', include(router.urls)
    ]


Some example usage
..................

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
