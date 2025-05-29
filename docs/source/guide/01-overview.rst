Overview
========

As explained before capabilities permission system provide access to objects only based on a :py:class:`~caps.models.access.Access`. This element provide: an identifier (uuid), a set of allowed actions to users (aka :py:class:`~caps.models.Capability`), and eventually an expiration date.

This figure shows how is it implemented in Django-Caps:

.. figure:: ../static/caps-models.drawio.png

    Every Object has an owner and can provide Access to other Agents. They are addressed by their uuid (for the owner) or by the access' uuid (for the receivers). The access provide permissions whose codename corresponds to Django's auth Permission.

Django-Caps provides views that will use the provided scheme in order to grant user access or actions.

:py:class:`~caps.models.object.Object`, :py:class:`~caps.models.access.Access`, models are ``abstract``. When Object is subclassed in a concrete model,
a concrete Access is generated (accessible from subclass scope). This ensure that:

- The Access models are associated to one object type, allowing reverse relations to be accessible (comparing to a solution involving ContentType framework). This also allows to joins table on SQL requests (thus prefetch values among other things);
- This ensures clear segregation for accesses and capabilities per object type and reduce tables sizes;


Access
------

An Object is always accessed through a access. An Object without a access must not be accessible to the user. This also means that once when an object is returned through API, the access MUST be provided.

As told, a Access provides a set of capabilities. Each capability grants two things: permission (access or action) and this permission to be share (or not).

A Access can be shared, which means that a new one will be created based one the current one. This creates a chains of parent-child accesses, ensuring control over the accesses. In Django-Caps, this process is called *derivation*, as a access is *derived* from another one.

The first access of this chain is the *root access*. There only can be one access for each object, which is owned by a single agent.

.. code-block::

    # Taking the example from index page
    from caps.models import Agent
    from .models import Post

    agent = Agent.objects.all()[0]
    agent_2 = Agent.objects.all()[2]

    # this raises ValueError: only one access is allowed
    post = Post.objects.filter(accesses__isnull=False).first()
    access = Post.Access.create_root(agent, post)


The root access will use the default capabilities as initial ones.


Create and update accesses
............................

There are only two ways for user (through views or API) to create a Access:

- By creating a :py:class:`~caps.models.objects.Object`: the related view will ensure the root access is created.
- By derivating an already existing access;

It is assumed that once a Access is created it can not be updated (nor its capabilities). This is in order to ensure the integrity of the whole chain of accesses. This is a current trade-off in Django-Caps that might change in the future even though it isn't planned.

If a user wants to update a Access (eg. add more capabilities), he should instead create a new access and eventually delete the older one. We ensure that all derived accesses will be destroyed at the same time of a parent (by cascading).


Expiration
..........

An expiration datetime can be provided for a Access. This allows to share an object for a limited time to someone else. Once the date is expired, the receiver can no longer access it.

Note: all derivated Access from one with an expiration will expire at this moment max.


Capability
----------

A Capability represent a single action or access to be granted. It also can grant sharing this permission. It can in
some way be looked as a through table of a Django's ``ManyToManyField`` although it not implemented as is
(due to technical reasons).

A default capability is the one provided by default when creating a root access. It is simply a capability without an assigned Access. Since a Capability table is created for each Object concrete sub-model, we are sure they will only target this sub-model.

When user derives a access, eg for allowing Alice to access the object, he can provide her the ability to reshare it
using :py:attr:`~caps.models.capability.Capability.max_derive` provide the maximum amount of derivation as an absolute
value relative to root. Each time a access is derived, the ``max_derive`` is decremented by one.

This implies that:

.. code-block:: python

    access = Access.objects.all().first()
    capability = access.capabilities.all().first()

    if capability.max_derive == 1:
        # this means that derived capability can't be reshared
        assert capability.derive().max_derive == 0
    elif capability.max_derive == 0:
        # this raises PermissionDenied, as capability can't be derived
        capability.derive()
    else:
        # this means that derived capability can't be shared
        assert not capability.derive(0).can_derive()

        # this means that derived capability can be reshared, as max_derive > 1
        assert capability.derive(1).can_derive()
