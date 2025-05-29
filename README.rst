Django-Caps
===========

Django-Caps provides capability based object permission system for Django applications.
This project is inspired by `Capn'Proto documentation <https://capnproto.org>`_ (`interesting paper <http://www.erights.org/elib/capability/ode/ode.pdf>`_).

A capability is a permission provided for a specific object. It can be *derived* (shared) a limited amount of time. Users never directly access the targeted object, but through a *access* that defines allowed capabilities for it.

In short, why use capabilities?

- *Granularity over objects permissions*
- *Reduced risk of privilege escalation*
- *Avoid direct access to database objects*

More in the guide, :ref:`Capability vs ACL permission systems`.


Features
--------

Here is what we provide:

- **Capability based object permissions system**: objects can be shared with specific permissions to user/group. The object is then accessed by this shared object rather than directly (except for its owner).
- **Access sharing**: Objects' accesses can be shared with granular control on permissions.
- **Integration**: authentication/permission backend is provided both for Django and Django Rest Framework. Views, viewsets and serializers too.
- **Agents**: users can act under different profiles, as a user or group. The accesses always target other agents.


Among other things:

- **Database id obfuscation**: object internal id are never exposed to the outside world. Instead uuid are used to reference them in API and urls. This mitigate attacks on predictive id.
