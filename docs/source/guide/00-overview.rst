Overview
========

As explained before capabilities permission system provide access to objects only based on a :py:class:`~caps.models.reference.Reference`. This element provide: an identifier (uuid), a set of allowed actions to users (aka :py:class:`~caps.models.Capability`), and eventually an expiration date.

This figure shows how is it implemented in Django-Caps:

.. figure:: ../static/caps-models.drawio.png

    The Object is accessed through its reference. A reference is assigned to an Agent which identifies the user. The reference provides capabilities which are linked to Django's auth Permission.

Django-Caps provides views that will use the provided scheme in order to grant user access or actions.

:py:class:`~caps.models.object.Object`, :py:class:`~caps.models.reference.Reference`,
:py:class:`~caps.models.capability.Capability` models are ``abstract``. When Object is subclassed in a concrete model,
a concrete Reference is generated (accessible from subclass scope). The same occurs between Reference and Capability.
This mechanism ensure different things:

- The Reference and Capability models are associated to one object type, allowing reverse relations to be accessible (comparing for example over a solution using ContentType framework). This also allows to joins table on SQL requests (thus prefetch values among other things);
- This ensure clear segregation for references and capabilities per object type and reduce tables sizes;
- We can exploit this mechanism for eg. default reference capabilities;


Reference
---------

An Object is always accessed through a reference. An Object without a reference must not be accessible to the user. This also means that once when an object is returned through API, the reference MUST be provided.

As told, a Reference provides a set of capabilities. Each capability grants two things: permission (access or action) and this permission to be share (or not).

A Reference can be shared, which means that a new one will be created based one the current one. This creates a chains of parent-child references, ensuring control over the accesses. In Django-Caps, this process is called *derivation*, as a reference is *derived* from another one.

The first reference of this chain is the *root reference*. There only can be one reference for each object, which is owned by a single agent.

.. code-block::

    # Taking the example from index page
    from caps.models import Agent
    from .models import Post

    agent = Agent.objects.all()[0]
    agent_2 = Agent.objects.all()[2]

    # this raises ValueError: only one reference is allowed
    post = Post.objects.filter(references__isnull=False).first()
    ref = Post.Reference.create_root(agent, post)


The root reference will use the default capabilities as initial ones.


Create and update references
............................

There are only two ways for user (through views or API) to create a Reference:

- By creating a :py:class:`~caps.models.objects.Object`: the related view will ensure the root reference is created.
- By derivating an already existing reference;

It is assumed that once a Reference is created it can not be updated (nor its capabilities). This is in order to ensure the integrity of the whole chain of references. This is a current trade-off in Django-Caps that might change in the future even though it isn't planned.

If a user wants to update a Reference (eg. add more capabilities), he should instead create a new reference and eventually delete the older one. We ensure that all derived references will be destroyed at the same time of a parent (by cascading).



Capability
----------

A Capability represent a single action or access to be granted. It also can grant sharing this permission. It can in
some way be looked as a through table of a Django's ``ManyToManyField`` although it not implemented as is
(due to technical reasons).

A default capability is the one provided by default when creating a root reference. It is simply a capability without an assigned Reference. Since a Capability table is created for each Object concrete sub-model, we are sure they will only target this sub-model.

When user derives a reference, eg for allowing Alice to access the object, he can provide her the ability to reshare it
using :py:attr:`~caps.models.capability.Capability.max_derive` provide the maximum amount of derivation as an absolute
value relative to root. Each time a reference is derived, the ``max_derive`` is decremented by one.

This implies that:

.. code-block:: python

    ref = Reference.objects.all().first()
    capability = ref.capabilities.all().first()

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
