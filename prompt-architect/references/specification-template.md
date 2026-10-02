# 24-Section Specification Template

Use this template when producing a master engineering specification via `prompt-architect`.
Include all 24 headings. For sections that do not apply, write: **Not applicable — [specific reason].**
Do not invent a database, AI subsystem, account system, or deployment platform merely to populate a section.

---

## 1. Role

*Who is responsible for this implementation and what expertise does the role require?*

Example: "Senior full-stack engineer with React, PostgreSQL, and REST API experience. Responsible for frontend, backend API, database schema, and deployment configuration."

---

## 2. Objective

*What is the concrete, single-sentence deliverable?*

Example: "Deliver a working task management application that allows users to create, assign, prioritize, and track tasks with real-time updates."

---

## 3. Product Vision

*Who uses this? What problem does it solve? What is the value?*

- **Target users:** [who]
- **Problem:** [what friction or gap exists today]
- **Value:** [what the user gains]
- **Scope boundary:** [what this product is not]

---

## 4. Core Concepts

*Domain terms, entities, and lifecycle states used throughout this specification.*

| Term | Definition |
|---|---|
| [Entity A] | [Definition and relationship to other entities] |
| [State] | [Lifecycle meaning] |

---

## 5. User Experience

*Primary user journeys, information hierarchy, and accessibility requirements.*

- **Primary journey:** [step-by-step flow for the core use case]
- **Secondary journeys:** [supporting use cases]
- **Accessibility:** WCAG 2.1 AA minimum. Keyboard-navigable. Focus-visible on all interactive elements. Sufficient color contrast (4.5:1 normal text, 3:1 large text).
- **Responsive breakpoints:** [specify or mark not applicable]

---

## 6. Functional Requirements

*Prioritized, stable requirement IDs. Use MUST/SHOULD/MAY.*

| ID | Priority | Requirement |
|---|---|---|
| FR-01 | MUST | [Core behavior — one sentence] |
| FR-02 | MUST | [Core behavior] |
| FR-03 | SHOULD | [Secondary behavior] |
| FR-04 | MAY | [Optional enhancement] |

---

## 7. Important Interactions

*Inputs, state transitions, feedback, keyboard behavior, and mobile behavior.*

- **[Action]:** [Expected transition, feedback, and timing]
- **Keyboard:** [Relevant shortcuts and focus management]
- **Mobile:** [Touch targets ≥ 44px; relevant gesture behavior]
- **Loading/error/empty states:** [Required behavior for each]

---

## 8. Data Model and Schemas

*Entities, relationships, validation rules, and persistence.*

Not applicable — [reason] OR:

```sql
-- Example schema
CREATE TABLE [table] (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  [field] [type] NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

- **Validation:** [required fields, format constraints, length limits]
- **Relationships:** [foreign keys, cascade behavior]
- **Persistence:** [where data lives, TTL if applicable]

---

## 9. Architecture and Layout

*Module boundaries, integrations, and proposed directory organization.*

```
[project-root]/
├── [module-a]/          # [responsibility]
│   ├── [file]
├── [module-b]/          # [responsibility]
└── [shared]/            # [shared contracts or utilities]
```

- **Module boundaries:** [what each module owns and what it does not]
- **Integration points:** [APIs, events, or shared contracts between modules]

---

## 10. Technology Choices

*Stack constraints, selected dependencies, and rationale.*

| Layer | Choice | Rationale |
|---|---|---|
| [Frontend] | [library/framework] | [why] |
| [Backend] | [runtime/framework] | [why] |
| [Database] | [engine] | [why] |

- **Assumptions:** [what is assumed about the environment]
- **Constraints:** [versions, licensing, existing dependencies to preserve]

---

## 11. Performance Requirements

*Measurable budgets appropriate to the product.*

| Metric | Target | Measurement method |
|---|---|---|
| [Page load / API response] | [e.g. < 200ms p95] | [how to measure] |

Not applicable — [reason] if no specific performance requirements exist.

---

## 12. Local and Offline Behavior

*Persistence strategy, connectivity loss handling, and synchronization.*

Not applicable — [reason] OR:

- **Local persistence:** [mechanism]
- **Offline behavior:** [what works without network; what degrades gracefully]
- **Sync on reconnect:** [strategy]

---

## 13. Security and Validation

*Trust boundaries, authorization model, and input handling.*

- **Authentication:** [mechanism or not applicable]
- **Authorization:** [who can access what; tenant isolation if relevant]
- **Input validation:** [where and how user input is sanitized]
- **Trust boundaries:** [what is trusted; what is untrusted]
- **Secrets handling:** [how credentials and tokens are managed]

---

## 14. Error Handling

*Failure states, retry behavior, recovery, and user-facing messages.*

| Failure | Behavior | User message |
|---|---|---|
| [Network error] | [retry N times, then show error state] | [copy] |
| [Validation error] | [inline feedback] | [copy] |
| [Server error] | [fallback or retry] | [copy] |

---

## 15. Edge Cases

*Relevant boundary conditions and unusual states.*

- [Empty state: what renders when there is no data]
- [Concurrent edit: behavior when two users modify the same resource]
- [Rate limit hit: behavior when upstream API returns 429]
- [Add other relevant edge cases]

---

## 16. AI Behavior

*Model or data boundaries, fallback behavior, and evaluation approach if AI is involved.*

Not applicable — [reason] OR:

- **Model used:** [name, version, provider]
- **Input boundary:** [what is sent to the model; what is never sent]
- **Output handling:** [how model output is validated before use]
- **Fallback:** [behavior when model is unavailable or returns malformed output]
- **Evaluation:** [how quality is measured]

---

## 17. Things Not to Build

*Explicit exclusions and prohibited shortcuts.*

- [Feature A] — [reason it is out of scope]
- [Shortcut B] — [reason it is prohibited]
- [Do not use X] — [reason]

---

## 18. MVP Scope

*Smallest useful, complete product slice. What must work end-to-end before anything else ships?*

- [Core flow A works end-to-end]
- [Core data model is persisted]
- [One happy-path test suite passes]
- [Explicitly not in MVP: list]

---

## 19. Future Phases

*Deliberately deferred capabilities. Include them here so they are not accidentally built in the MVP.*

- **Phase 2:** [Feature X — deferred because Y]
- **Phase 3:** [Feature Z — deferred because W]

---

## 20. Implementation Constraints and Dependencies

*Coarse sequencing constraints. Not a detailed task schedule.*

- [Component A must exist before Component B can be built]
- [External API contract must be confirmed before schema is finalized]
- [Migration must run before new code is deployed]

---

## 21. Testing Requirements

*Observable behaviors and meaningful verification requirements.*

- **Unit tests:** [what units require isolation testing and why]
- **Integration tests:** [which boundaries require contract testing]
- **End-to-end:** [which user journeys must be verified by running the actual system]
- **Anti-tautology rule:** Tests must verify observable side-effects (database rows, HTTP responses, rendered output), not just that a function was called.
- **Explicit exclusions:** [what does not need automated tests and why]

---

## 22. Success Criteria

*Acceptance IDs and measurable completion conditions.*

| ID | Condition | Measurement |
|---|---|---|
| A-01 | [Observable outcome] | [How to verify] |
| A-02 | [Observable outcome] | [How to verify] |

---

## 23. Final Delivery Checklist

*Required artifacts, documentation, and validation evidence.*

- [ ] All acceptance criteria A-01 through A-N verified and evidence recorded
- [ ] Working tree clean; all changes committed with meaningful messages
- [ ] README updated if public interfaces changed
- [ ] Migration scripts tested on a clean schema
- [ ] [Other artifacts specific to this product]

---

## 24. Observability and Operations

*Logging, health checks, troubleshooting, backups, and recovery where applicable.*

Not applicable — [reason] OR:

- **Logging:** [what is logged, at what level, and where]
- **Health checks:** [endpoint or mechanism]
- **Alerting:** [what conditions trigger alerts]
- **Backup and recovery:** [strategy and RTO/RPO targets if applicable]
- **Troubleshooting:** [known failure modes and diagnostic steps]
