# Architecture Decision Record (ADR) Template

Format for recording consequential architectural decisions in `docs/adr/NNNN-[title].md`. Based on the Michael Nygard / MADR standard.

---

```markdown
# ADR-0001: [Short Title of Architectural Decision]

- **Status**: [Proposed | Accepted | Deprecated | Superseded by ADR-XXXX]
- **Date**: [YYYY-MM-DD]
- **Deciders**: [Core Team / Lead Architect]
- **Technical Story**: [Link to issue, RFC, or requirements]

---

## 1. Context and Problem Statement

[Describe the context, technical challenges, and forces influencing the decision. What problem are we solving? Why does a default or naive approach fail?]

Example:
> We are scaling the codebase from a single-developer prototype to a multi-domain platform. In our prior monolithic layered structure (`controllers/`, `models/`), changes to one domain frequently broke unrelated routes, and AI agents suffered from prompt amnesia when reading large files.

---

## 2. Decision Drivers

- Need hermetic module isolation to prevent cascading cross-file regressions.
- Need bounded LLM working context (target ~400–600 lines per slice task; cohesive modules up to 1,200–1,500 LOC) per development task.
- Need mechanical boundary enforcement in CI.

---

## 3. Considered Options

1. **Option 1**: Layered Architecture with global models (`src/models`, `src/controllers`).
2. **Option 2**: Distributed Microservices across multiple git repositories.
3. **Option 3**: **Vertical Slice Architecture** within a modular monorepo.

---

## 4. Decision Outcome

Chosen option: **Option 3: Vertical Slice Architecture**, because it delivers the isolation benefits of microservices without the operational overhead of distributed networks and separate repositories.

### Positive Consequences
- Every module (`modules/<slice>/`) is self-contained with its own contract, service, routes, and tests.
- Cross-slice imports are restricted to public `contract.ts` boundaries and checked in code review / ESLint.
- Tasks can be planned and executed within a bounded slice context window.

### Negative Consequences & Trade-offs
- Duplication of minor helper utilities across slices is preferred over shared mutable coupling.
- Cross-slice interactions require defining an explicit public `contract.ts` or publishing to an event bus.

---

## 5. Compliance & Invariants

1. All new features must be placed in `src/modules/<slice>/`.
2. Slices must never import sibling slice internal files (`service.ts`, `routes.ts`).
3. All tests and boundary/lint checks must return exit code 0 before merging.
```
