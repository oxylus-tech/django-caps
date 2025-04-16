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
- Django views and mixins;
- Django Rest Framework views, viewsets and serializers;
- A user can act under different profiles (agents);

Models
......

The current implementation provides the following models:

- ``Capability``: a single access right link to a specific action;
- ``Reference``: reference to an object, linked to an agent and a set of capabilities;
- ``Agent``: either an user or a group.

  Note: although capabilities are primarely designed to target only users, reducing ambient privilege (see below), we allow to assign them on groups. This allows to use capability-like system for object permissions on use-case not primarely targetted.

- ``Object``: objects to be accessed through references.
