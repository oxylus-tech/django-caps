TODO
====

- models:

    - CapabilitySet -> derive_caps arg to ease api usage
    x Reference -> expiration date on derived References.

- migrations/signal:

    - Provide a way to specify default Capabilities which will be
      created on migration.
    - create an agent for each user and each group

- views:

    x views for: Agent (list, detail -> Permission required), Reference (list, detail, delete)
    - Reference: derive
    x viewsets for: Reference, Capability

- CRON:
    - clear expired references
