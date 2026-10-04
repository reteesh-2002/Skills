# Vertical Slice Architecture Template

Use this reference when `create-architect` produces the module directory scaffold for Decision 3b. Every project — from a 2,000-line prototype to a 50,000-line production system — adopts this layout so that the agent never needs more than 600 lines in context per task.

---

## Directory Scaffold

```
src/
├── core/                          # Shared frozen primitives ONLY
│   ├── db.ts                      # Single database client / connection pool
│   ├── auth.ts                    # Session resolution + tenant context
│   ├── logger.ts                  # Structured JSON logger
│   └── events.ts                  # In-process event bus (optional)
│
└── modules/
    ├── <slice-a>/                 # Example: "billing"
    │   ├── contract.ts            # Frozen public interface (< 50 lines)
    │   ├── routes.ts              # HTTP / RPC handlers
    │   ├── service.ts             # Pure domain logic (< 200 lines)
    │   └── billing.test.ts        # Colocated integration tests
    │
    ├── <slice-b>/                 # Example: "portfolio"
    │   ├── contract.ts
    │   ├── routes.ts
    │   ├── service.ts
    │   └── portfolio.test.ts
    │
    └── <slice-c>/                 # Example: "notifications"
        ├── contract.ts
        ├── routes.ts
        ├── service.ts
        └── notifications.test.ts
```

---

## The Non-Negotiable Cross-Slice Import Rule

```
✅ ALLOWED:  import { CreateInvoiceInput } from '../billing/contract'
✅ ALLOWED:  eventBus.emit('invoice.created', payload)
❌ BLOCKED:  import { calculateTax } from '../billing/service'
❌ BLOCKED:  import { db } from '../portfolio/db'
```

**Why this matters for scalability:**
- When an agent works on `portfolio/`, it loads ONLY: `contract.ts` + `service.ts` + `portfolio.test.ts` (~400–600 lines total).
- The remaining 30,000 lines of the codebase stay invisible — zero context dilution, zero attention drift, zero regressions introduced by context pollution.
- Enforce this automatically with `eslint-plugin-import` boundary rules or TypeScript project references.

---

## `contract.ts` Stub (Zod / TypeScript)

Every slice exposes only a typed, validated contract. Nothing else leaks out.

```typescript
// modules/billing/contract.ts
import { z } from 'zod'

// Input schemas — validated at the route boundary
export const CreateInvoiceSchema = z.object({
  tenantId: z.string().uuid(),
  customerId: z.string().uuid(),
  lineItems: z.array(z.object({
    description: z.string().min(1),
    amountCents: z.number().int().positive(),
  })).min(1),
  dueDateIso: z.string().datetime(),
})

// Output types — what callers receive
export type CreateInvoiceInput = z.infer<typeof CreateInvoiceSchema>

export type InvoiceRecord = {
  id: string
  tenantId: string
  status: 'draft' | 'pending' | 'paid' | 'void'
  totalCents: number
  createdAt: string
}
```

---

## The Missing 70% — Schema Scaffold

The defensive enterprise layers that turn a 3,000-line happy-path app into a 20,000-line production system. Include the relevant tables in Decision 3a of the blueprint.

### 1. Tenant Scoping (Multi-Tenancy)
```sql
-- Every query must include WHERE tenant_id = $current_tenant_id
CREATE TABLE organizations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add tenant_id to every domain table
ALTER TABLE invoices ADD COLUMN tenant_id UUID NOT NULL REFERENCES organizations(id);
CREATE INDEX idx_invoices_tenant ON invoices(tenant_id);
```

### 2. State Machine Transitions
```sql
-- Explicit status enum prevents invalid states
CREATE TYPE invoice_status AS ENUM ('draft', 'pending', 'paid', 'void');

CREATE TABLE invoice_transitions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  invoice_id    UUID NOT NULL REFERENCES invoices(id),
  from_status   invoice_status NOT NULL,
  to_status     invoice_status NOT NULL,
  actor_id      UUID NOT NULL REFERENCES users(id),
  transitioned_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 3. Immutable Audit Ledger
```sql
-- Append-only: never UPDATE or DELETE rows in this table
CREATE TABLE audit_log (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES organizations(id),
  actor_id    UUID REFERENCES users(id),
  action      TEXT NOT NULL,      -- e.g. 'invoice.created', 'user.deleted'
  resource_id UUID,               -- ID of the affected record
  payload     JSONB,              -- Sanitized snapshot (no credentials)
  ip_address  INET,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_tenant_time ON audit_log(tenant_id, created_at DESC);
```

### 4. Background Job Outbox (Idempotent Async)
```sql
-- Write-ahead outbox: insert before the transaction commits
CREATE TABLE outbox_events (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type    TEXT NOT NULL,    -- e.g. 'invoice.send_email'
  payload       JSONB NOT NULL,
  status        TEXT NOT NULL DEFAULT 'pending', -- pending | processing | done | failed
  attempts      INT NOT NULL DEFAULT 0,
  next_retry_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_outbox_pending ON outbox_events(status, next_retry_at) WHERE status IN ('pending', 'failed');
```

---

## Sub-600 LOC Context Ceiling

When an agent implements or modifies a slice, it must load only:

| File | Approximate Lines |
|---|---|
| `modules/<slice>/contract.ts` | ~50 lines |
| `modules/<slice>/service.ts` | ~150–200 lines |
| `modules/<slice>/routes.ts` | ~100–150 lines |
| `modules/<slice>/<slice>.test.ts` | ~150–200 lines |
| **Total in context** | **~450–600 lines** |

The remaining 29,400 lines of a 30,000-line codebase remain invisible. This is how an agent scales past the 3,000-line ceiling without context collapse or regression loops.
