.. _Capability vs ACL permission systems:

Capability vs ACL permission systems
====================================

#. Granular and Delegable Access Control

    - In a capability-based system, access rights are directly assigned to objects (capabilities) rather than being centrally managed per resource.
    - Advantage: Users can delegate access rights without requiring modifications to a central policy (e.g., passing a token or capability access to another user).
    - In contrast: ACLs require explicit permission modifications on the resource, which can be complex and require admin intervention.

#. Reduced Need for a Central Authority

    - Capabilities are typically self-contained (e.g., a token, key, or access) and grant access upon presentation.
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

    This however still can be usable for object permissions by providing accesses for groups instead of users.
