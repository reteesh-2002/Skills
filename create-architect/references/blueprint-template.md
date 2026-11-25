# Inside-Out Engineering Blueprint Template

Use this template when producing an engineering architecture blueprint via `create-architect`.
Focus strictly on practical technical decisions: Data Flow, Tech Stack, Data Model, API/UI contracts, and the Inside-Out build sequence. Zero bureaucratic fluff.

---

# [Project Name] — Engineering Blueprint

### Executive Intent
- **Goal**: [One sentence describing the concrete product delivered]
- **Target User**: [Who uses this and what value they gain]

---

## 1. Data Flow Architecture
Trace how data moves through the application:
```
[User / External Input] ──> [Validation & Processing Engine] ──> [Database / Persistence] ──> [UI / Consumers]
```
- **Inflow**: [Where data enters: forms, webhooks, file uploads, third-party APIs]
- **Transformations**: [Calculations, format conversions, business rules, AI summarization]
- **Storage**: [Persistent tables, relational foreign keys, caches]
- **Outflow**: [Rendered UI views, real-time events, exports, webhooks]

---

## 2. Pragmatic Tech Stack
Choose the simplest, battle-tested stack matching the requirements:

| Layer | Technology Choice | Rationale |
|---|---|---|
| **Backend & Runtime** | [e.g. Next.js App Router / FastAPI / Express] | [Why this fits the workload] |
| **Database & ORM** | [e.g. PostgreSQL + Drizzle ORM / SQLite] | [Relational integrity, migrations] |
| **Frontend & UI** | [e.g. React + Tailwind CSS] | [Modern component architecture] |
| **Design Aesthetic** | [e.g. Linear Dark / Apple Glass / Stripe] | [Matches product domain] |
| **Motion & Effects** | [e.g. Parallax Hero / Sticky Stacking / Static] | [Tactile UX standard] |

---

## 3. Data Model & Schemas (The Backbone)
Define exact relational schemas, constraints, foreign keys, and seed data:

```sql
-- Core entities
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE [entities] (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  [field] [type] NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Seed Data (Mandatory)
Never develop against an empty database. Define at least 2–3 realistic initial records:
- `Entity 1`: [Realistic sample values]
- `Entity 2`: [Realistic sample values]

---

## 4. API & The 4 Screen States Contract

### A. Endpoints
- `GET /api/[resource]` — Fetch list (supports pagination & filtering)
- `POST /api/[resource]` — Create record (validates required fields)
- `GET /api/[resource]/:id` — Fetch single record with relations
- `PATCH /api/[resource]/:id` — Update record
- `DELETE /api/[resource]/:id` — Delete record

### B. The 4 Mandatory Screen States
Every screen must define all four UI states:
1. **Empty State**: Welcoming onboarding card with clear CTA when zero items exist.
2. **Loading State**: Dimension-stable skeleton placeholders matching real content layout (no CLS).
3. **Success State**: Rich interactive components, tables, and cards styled with chosen design preset.
4. **Error State**: Non-blocking toast or banner explaining the failure with a retry action.

---

## 5. Inside-Out Build Sequence
Sequence the implementation from the foundation up:

- **Phase 1: Foundation (Database & Schema)**
  - Write schema, relations, and migrations (`schema-craft`).
  - Insert initial seed data and verify query execution.
- **Phase 2: Core Engine (API & Business Logic)**
  - Implement endpoints with input validation.
  - Verify endpoint status codes and payloads with integration tests.
- **Phase 3: The Interface (Frontend & 4 UI States)**
  - Hand off to `frontend-artisan`: apply design preset & parallax/motion effects.
  - Implement all 4 screen states (Empty, Loading, Success, Error).
- **Phase 4: Verification**
  - Run `qa-sentinel`: verify `exit 0` and real tests executed (`passed == collected`).

---

## 6. Module Directory Scaffold (Vertical Slice Layout)
List all planned modules and their root files. No flat `controllers/` or `models/` directories.

```
src/
├── core/                    # Shared frozen primitives
│   ├── db.ts
│   ├── auth.ts
│   └── logger.ts
└── modules/
    ├── [slice-a]/
    │   ├── contract.ts      # < 50 lines — public Zod/TypeScript interface only
    │   ├── routes.ts        # HTTP handlers
    │   ├── service.ts       # Cohesive domain logic
    │   └── [slice-a].test.ts
    └── [slice-b]/
        ├── contract.ts
        ├── routes.ts
        ├── service.ts
        └── [slice-b].test.ts
```

**Cross-Slice Import Rule**: Slices communicate only via `contract.ts` or the event bus. Never import a peer slice's `service.ts` or internal files.

---

## 7. Missing 70% Checklist
Mark each layer as **Required**, **Not Required**, or **Deferred** for this project. Leaving all unchecked means the project will cap at ~3,000 lines.

| Defensive Layer | Status | Implementation Note |
|---|---|---|
| **Tenant Scoping & RLS** | [ ] Required / [ ] Not Required | Every query filtered by `tenant_id`; Row-Level Security policies |
| **Explicit State Machines** | [ ] Required / [ ] Not Required | Enumerated transitions + guard validation |
| **Background Jobs & Retry Queue** | [ ] Required / [ ] Deferred | Outbox pattern; dead-letter handling |
| **Immutable Audit Ledger** | [ ] Required / [ ] Not Required | Append-only table: actor, action, resource, timestamp |
| **Input Sanitization Boundaries** | ✅ Always Required | Zod/Pydantic at every API boundary |
| **RBAC / Permission Guards** | [ ] Required / [ ] Not Required | Deny-by-default middleware on every authenticated route |

