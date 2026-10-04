---
name: create-architect
description: Pragmatic project design and architecture engine. Translates raw ideas into concrete engineering decisions (Data Flow, Tech Stack, Data Model/Schema, API contracts, and the 4 mandatory UI states). Enforces an Inside-Out build sequence (DB -> API -> UI -> Verify). Use when designing or architecting a new project or major feature.
---

# Create Architect

Translate raw ideas into an **Inside-Out Engineering Blueprint** — a grounded, pragmatic architecture document that makes the critical engineering decisions before coding begins.

`create-architect` does not write 24-section bureaucratic waterfall documents. It defines the software the way real staff engineers design systems: **Data Flow → Tech Stack → Data Model → API & 4 UI States → Inside-Out Build Sequence**.

---

## 1. Activation and Boundaries

**Activate when the user asks to:**
- Design, architect, structure, or plan a new project, application, or system from scratch.
- Direct invocation: `$create-architect`, `@create-architect`.

**Do not activate for:**
- Bug fixes, single-file edits, or small refactors → use `deep-debugger` or implement directly.
- Task-by-task execution schedules → use `plan-master`.
- Routine UI styling or visual changes → use `frontend-artisan`.

**Action boundaries:**
- Read user-specified repositories, files, and schemas to ground the blueprint.
- Do not invent speculative abstractions, microservices, or enterprise compliance checklists for a simple application.
- Preserve an established tech stack and design system unless the user explicitly requests changes.

---

## 2. The 5 Core Engineering Decisions

Every project blueprint produced by `create-architect` must define these five decisions:

### Decision 1: Data Flow Architecture
Trace how information moves like water through a pipe:
1. **Inflow**: Where does data enter? (User form inputs, external webhooks, file uploads, third-party APIs).
2. **Transformations**: What computations happen? (Validation, business rules, format conversions, AI generation).
3. **Storage**: Where does it persist? (Relational PostgreSQL/SQLite tables, Redis caches, object storage).
4. **Outflow**: How does the user see or receive it? (Interactive tables, dashboard charts, real-time events, exports).

### Decision 2: Pragmatic Tech Stack
Select the simplest, battle-tested stack matching the requirements:
- **Backend / API**: Node/TypeScript (Next.js App Router, Express) or Python (FastAPI, Django).
- **Database**: PostgreSQL (relational integrity, migrations) or SQLite (lightweight/local prototypes).
- **Frontend**: React + Tailwind CSS.
- **Design Aesthetic & Motion**: Select from [`frontend-artisan/references/design-presets.md`](../frontend-artisan/references/design-presets.md) (e.g. *Linear Dark*, *Apple Glass*, *Stripe*) and [`frontend-artisan/references/motion-effects.md`](../frontend-artisan/references/motion-effects.md) (e.g. *Multi-Layer Parallax*, *Sticky Cards*).

### Decision 3: Data Model, Schema & Vertical Slice Layout (The Backbone)
Software is mostly views over a database. Define entities, relationships, seed data, **and** the module directory structure:

**3a. Relational Schema:**
- Tables, column data types, foreign keys, and cascading delete behaviors.
- Validation constraints (unique keys, not-null, check constraints).
- **Mandatory Seed Data**: Specify 2–3 realistic records so development never starts against empty tables.

**3b. Vertical Slice Module Layout (required for every project):**
Every project must adopt a domain-bounded vertical slice structure — not flat layers (`controllers/`, `models/`):
```
src/
├── core/                    # Shared frozen primitives only
│   ├── db.ts                # Database client
│   ├── auth.ts              # Session + tenant context
│   └── logger.ts            # Structured logging
└── modules/
    └── <slice-name>/        # One directory per domain
        ├── contract.ts      # Frozen public interface (Zod/TypeScript, < 50 lines)
        ├── routes.ts        # HTTP / RPC handlers
        ├── service.ts       # Pure domain logic (< 200 lines)
        └── <slice>.test.ts  # Colocated integration tests
```

**Cross-Slice Import Rule (mandatory invariant):**
- Modules communicate **only** through their own `contract.ts` or a shared event bus.
- Direct imports of peer slice internals (e.g. `import { x } from '../billing/service'`) are strictly forbidden.
- This invariant keeps the agent context below 600 lines per task and prevents cascading regressions as the codebase scales past 10,000 lines.

See [`references/vertical-slice-template.md`](references/vertical-slice-template.md) for the full scaffold with contract stubs.

### Decision 4: API, 4 Screen States Contract & The Missing 70%
**4a. API Endpoints:**
- Clear HTTP methods and payloads (`GET /api/items`, `POST /api/items`, `PATCH /api/items/:id`).

**4b. The 4 Mandatory Screen States**: For every screen or view, define:
  1. **Empty State**: Welcoming illustration or onboarding prompt when zero items exist.
  2. **Loading State**: Dimension-stable skeleton placeholders matching final content layout.
  3. **Success State**: Rich interactive components, tables, and cards styled with chosen design preset.
  4. **Error State**: Non-blocking toast or banner with clear failure copy and a retry action.

**4c. The Missing 70% — required for production-grade systems:**
Real production software is ~70% defensive infrastructure, not happy-path CRUD. Every blueprint must specify which of these layers apply and how they are implemented. Omitting this section is what caps AI-generated codebases at 3,000 lines.

| Layer | Description | When Required |
|---|---|---|
| **Tenant Scoping & RLS** | Every query filtered by `tenant_id` / `org_id`; database Row-Level Security | Multi-user or SaaS apps |
| **Explicit State Machines** | Enumerated valid transitions with guard validation (`Draft → Approved`) | Multi-step workflows |
| **Background Jobs & Retry Queue** | Outbox pattern; idempotent async retries with dead-letter handling | Emails, webhooks, long tasks |
| **Immutable Audit Ledger** | Append-only table: actor, action, resource, timestamp | Any state-mutating write |
| **Input Sanitization Boundaries** | Zod/Pydantic at every API boundary; reject unexpected fields | All endpoints |
| **RBAC / Permission Guards** | Route-level role checks; deny-by-default middleware | Any authenticated surface |

### Decision 5: Inside-Out Build Sequence
Order tasks strictly from the ground up:
- **Phase 1: Foundation** — Database tables, relations, vertical slice scaffold, and initial seed data.
- **Phase 2: Core Engine** — Backend routes, input validation, and endpoint tests per slice.
- **Phase 3: The Interface** — UI components, design preset styling, motion effects, and all 4 screen states.
- **Phase 4: Verification** — Proving real tests pass (`exit 0`, `collected > 0`, `passed == collected`).

---

## 3. Output Format

When activated, produce an **Engineering Blueprint** adhering to [`references/blueprint-template.md`](references/blueprint-template.md):
1. **Executive Intent**: Single-sentence goal and target user.
2. **Data Flow**: Inflow → Transformation → Storage → Outflow.
3. **Tech Stack**: Backend, Database, Frontend, Design Preset, and Motion Style.
4. **Data Model & Module Layout**: SQL/ORM schemas with foreign keys, seed data, and vertical slice directory scaffold.
5. **API, 4 UI States & Missing 70%**: Endpoint contract, UI states, and required defensive layers.
6. **Inside-Out Sequence**: Clear phased order ready for `plan-master`.

---

## Reference files

- [`references/blueprint-template.md`](references/blueprint-template.md) — Inside-Out Engineering Blueprint template
- [`references/vertical-slice-template.md`](references/vertical-slice-template.md) — Vertical slice scaffold with contract.ts stubs and Missing 70% schema
- [`../frontend-artisan/references/design-presets.md`](../frontend-artisan/references/design-presets.md) — 11 brand design presets
- [`../frontend-artisan/references/motion-effects.md`](../frontend-artisan/references/motion-effects.md) — Parallax, sticky stacking, 3D tilt effects
