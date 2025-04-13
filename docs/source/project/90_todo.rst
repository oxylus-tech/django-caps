TODO
====

- models:

    - CapabilitySet -> derive_caps arg to ease api usage

- migrations/signal:

    - Provide a way to specify default Capabilities which will be
      created on migration.
    - create an agent for each user and each group

- views:

    - views for: Agent
    - viewsets for: Reference, Capability

- serializers:

    - simple serializers
    - full serializers (nested):

        - Reference.capability
        - Object.reference

    - generate ModelSerializer based on provided object.

- filtersets:

    - for: Reference, Capability, Agent, Object

- forms
- admin
