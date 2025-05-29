TODO
====

- models:

    - CapabilitySet -> derive_caps arg to ease api usage
    x Access -> expiration date on derived Accesss.

- migrations/signal:

    - Provide a way to specify default Capabilities which will be
      created on migration.
    - create an agent for each user and each group

- views:

    x views for: Agent (list, detail -> Permission required), Access (list, detail, delete)
    - Access: derive
    x viewsets for: Access, Capability

- CRON:
    - clear expired accesses
