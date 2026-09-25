# Frozen Contract Format

Read at Phase 1.5, only when workstreams share types, state, or boundary calls.

Write the contract once, then paste it verbatim into every worker prompt. Workers MUST NOT edit it.

## Template

```
CONTRACT v<n> (frozen)
Owner of this file: Boss

1. Shared types / schemas
   <type or schema definitions in the project's own language>

2. Boundary signatures (function, endpoint, or event)
   <name>(<params>) -> <return>   # producer: Worker <X>, consumer: Worker <Y>
   Errors: <error shape and codes>

3. Invariants
   - <e.g. IDs are UUID strings; timestamps are UTC ISO-8601>

4. Ownership
   Worker A: <paths>
   Worker B: <paths>
   Boss only: manifests, lockfiles, registries, config, this contract
```

## Rules
- Use the project's real language and types (TS interfaces, Python dataclasses, OpenAPI, SQL DDL), not prose.
- Every boundary names one producer and its consumers.
- If a worker reports a missing field, the Boss revises the contract (bump version), then re-sends it to every affected worker.
- Phase 4 integration checks each boundary signature against this file.
