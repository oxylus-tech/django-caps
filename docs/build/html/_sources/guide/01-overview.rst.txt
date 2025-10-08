Overview
========

The system is designed to support fine-grained, shareable permissions across users, groups, and anonymous agents, while maintaining clear constraints on how far permissions can be redistributed.

Each :py:class:`caps.models.owned.Owned` declares its own permission policy via a class-level :py:attr:`caps.models.owned.Owned.root_grants` definition, while access instances are represented by Access entries, which may themselves be shared according to configurable depth constraints.

The :py:class:`caps.models.access.Access` defines what actions an agent can perform on a given object, and whether those permissions can be further shared. The :py:class:`caps.models.agent.Agent` model provides a unified interface for addressing users, groups, and public (unauthenticated) access.

.. figure:: ../static/caps-models.drawio.png

    Every Owned has an owner and can provide Access to other Agents. They are addressed by their uuid (for the owner) or by the access' uuid (for the receivers). The access provide permissions whose codename corresponds to Django's auth Permission.

Django-Caps provides views that will use the provided scheme in order to grant user access or actions.

Access to objects is governed as follows:

- The *owner* of an object can access it directly using the object's ``uuid``.
- Other agents must use the ``uuid`` of an ``Access`` grant they have received to interact with the object indirectly and within the scope of the permissions defined in that grant.


Core Models
-----------

The system is composed of three core models:

- ``caps.models.owned.Owned``
  Represents the resource being protected. Each object has a globally unique ``uuid`` and defines its available permissions through a class-level ``root_grants`` dictionary. This dictionary specifies which permissions are grantable and how many levels deep each one can be reshared.

- ``caps.models.agent.Agent``
  A unified abstraction of a permission recipient. An ``Agent`` may represent a specific user, a group of users, or an anonymous entity. This model decouples access logic from Django's built-in user and group models, enabling flexible and consistent permission targeting.

- ``caps.models.access.Access``
  Encapsulates a delegated permission. Each ``Access`` instance links a target ``Owned`` to a receiving ``Agent`` and contains a ``grants`` dictionary, where each key is a permission codename (e.g., ``"app.view_object"``) and each value is a reshare depth. This depth determines how many times the permission can be reshared down the access chain.


:py:class:`~caps.models.owned.Owned` and :py:class:`~caps.models.access.Access` models are ``abstract``. When Owned is subclassed in a concrete model,
a concrete Access is generated (accessible from subclass scope). This ensure that:

- The Access models are associated to one object type, allowing reverse relations to be accessible (comparing to a solution involving ContentType framework). This also allows to joins table on SQL requests (thus prefetch values among other things);
- This ensures clear segregation for accesses and capabilities per object type and reduce tables sizes;


Create and update Access
........................

There are only two ways for user (through views or API) to create a Access:

- By creating a :py:class:`~caps.models.owneds.Owned`: the related view will ensure the root access is created.
- By derivating an already existing access;

It is assumed that once a Access is created it can not be updated (nor its capabilities). This is in order to ensure the integrity of the whole chain of accesses. This is a current trade-off in Django-Caps that might change in the future even though it isn't planned.

If a user wants to update a Access (eg. add more capabilities), he should instead create a new access and eventually delete the older one. We ensure that all derived accesses will be destroyed at the same time of a parent (by cascading).


Access expiration
.................

An expiration datetime can be provided for a Access. This allows to share an object for a limited time to someone else. Once the date is expired, the receiver can no longer access it.

Note: all reshared Access from one with an expiration will expire at this moment max.


Usage Example
-------------

This section illustrates how to use the permission model to delegate access and verify permissions.

We use the ``Post`` model described in :ref:`quickstart` (read it  for more usage examples and setup).


Granting Access from an Owned
..............................

An object owner can share the object with another agent using the ``post.share(...)`` method (:py:meth:`caps.models.owned.Owned.share`). This method creates a new ``Access`` instance and assigns permissions according to the object's ``root_grants``.

.. code-block:: python

    # Assuming post is an instance of Post owned by the user
    # and agent_b is an instance of Agent representing the receiver

    # Using default grants
    access = post.share(agent_b)

    grant = {
        "app.view_post": 2,
        "app.change_post": 1,
    }

    access = post.share(agent_b, grant=grant)

    # access is now an Access instance linking obj to agent_b

Resharing an Access
...................

An agent who received access to an object can reshare it, as long as the reshare depth allows it. This is done using the ``access.share(...)`` method (:py:meth:`caps.models.access.Access.share`).

.. code-block:: python

    # Assuming access is an Access instance received by agent_b
    # and agent_c is another Agent who should receive limited access

    # Using defaults: this provide allowed reshared permission with share depth minus 1
    reshared_access = access.share(agent_c)

    # Using explicit permissions
    reshared_grant = {
        "app.view_post": 1  # Reshare depth reduced by one
    }

    reshared_access = access.share(agent_c, reshared_grant)

    # reshared_access allows agent_c to view the object and possibly reshare it once more

Permission Check
................

To check if a user has a given permission on an object, use Django’s standard ``has_perm`` API. Under the hood, your custom object permission backend should evaluate the user's linked Agent and relevant Access entries.

.. code-block:: python

    if user.has_perm("app.view_post", obj):
        print("User is allowed to view the post")
    else:
        print("Access denied")

The backend should resolve:

1. Whether the user is the owner of the object, or
2. Whether the user is linked to an Agent that has an ``Access`` entry to the object with the given permission.

``has_perm`` integrates cleanly with Django's permission system and can be used consistently in views, templates, or API logic.
