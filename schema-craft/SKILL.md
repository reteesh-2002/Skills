---
name: schema-craft
description: Database architecture, safe migrations, and type-safe API contract engine. Enforces production indexing strategies (foreign keys, compound queries), strict relational integrity (cascades, check constraints), zero-downtime migration protocols, and realistic edge-case seed data generation across PostgreSQL, SQLite, Prisma, Drizzle, and Django ORM. Use when designing data models, writing migrations, optimizing slow queries, or defining API contracts.
---

# Schema Craft

Production database architecture, safe migration engineering, and relational integrity. Prevents silent performance cliffs, orphaned data, and breaking migration accidents across full-stack applications.

---

## 1. Production Database Invariants

When designing schemas or migrations, enforce these core invariants:

1. **Foreign Key Indexing**: In PostgreSQL and MySQL, foreign keys are not automatically indexed by default. Unindexed FKs cause table/row lock escalation during parent record deletes and slow joins. Index FKs where join or deletion contention is anticipated.
2. **Explicit Delete Behavior**: Every relationship must specify explicit cascading semantics: `ON DELETE CASCADE`, `ON DELETE SET NULL`, or `ON DELETE RESTRICT`. Never leave it implicit.
3. **Timezone-Aware Timestamps**: Use timezone-aware timestamps (`TIMESTAMPTZ` in Postgres, ISO-8601 strings in SQLite/Prisma). Never store local naive datetimes.
4. **Target-DB Specific Migration Evidence**: Avoid broad "zero-lock" claims. Evaluate lock behavior against the target database engine (e.g., PostgreSQL supports `CREATE INDEX CONCURRENTLY` outside transactions; SQLite acquires an exclusive database lock during writes). Rehearse migrations against a disposable representative database.
5. **Safe Column Addition**: Never add a `NOT NULL` column to an existing table without a default value or a multi-phase backfill strategy.
6. **Destructive Action Safety**: Never run destructive DDL (`DROP TABLE`, `DROP COLUMN`, `TRUNCATE`) without explicit confirmation and an archival alternative.

---

## 2. Targeted ORM Adapter Selection

Detect the active stack and load **only the single relevant ORM adapter** rather than outputting multi-stack boilerplate:

- **Prisma (`schema.prisma`)**: Define models, relations (`@relation`), and composite indices (`@@index([fieldA, fieldB(sort: Desc)])`).
- **Drizzle ORM (`schema.ts`)**: Define tables using target dialect core (`pgTable`, `sqliteTable`, `mysqlTable`), explicit relations, and foreign key cascades.
- **Django ORM (`models.py`)**: Define models with `db_index=True`, `on_delete=models.CASCADE/PROTECT`, and `Meta.indexes = [models.Index(...)]`.
- **Raw SQL**: Idiomatic DDL with table constraints, default timestamps, and indexes tailored to the database engine.

---

## 3. Query-Driven Indexing Strategy

Index for demonstrated or anticipated query patterns rather than indexing every column universally:
- **Composite Indexes (ESR Rule)**:
  1. Equality columns first: `tenant_id = '...'`
  2. Sort columns second: `ORDER BY created_at DESC`
  3. Range filter columns last: `score > 80`
  - Example: `CREATE INDEX idx_orders_tenant_date ON orders (tenant_id, created_at DESC);`
- **Engine-Specific Indexing**:
  - **PostgreSQL**: Use `CREATE INDEX CONCURRENTLY` in non-transactional migrations for high-traffic tables.
  - **SQLite**: Keep indexes compact; index for point lookups and range scans.
  - **Partial Indexes**: For soft-deleted tables (`deleted_at IS NOT NULL`), use partial indexes (`WHERE deleted_at IS NULL`) to keep active indexes compact.

---

## 4. Minimal Relevant Seed Generation

Generate minimal, targeted seed fixtures that validate key data boundaries without unnecessary bulk:
1. **Unicode & Internationalization**: Accent characters (`José Müller`), non-Latin scripts, emoji handles.
2. **Boundary Lengths**: Empty/null strings where permitted, minimum string (1 char), maximum column boundaries.
3. **Relational Integrity**: 1:1, 1:N, and optional relations represented with valid foreign key references.
4. **Temporal Spread**: Records with past, current, and future timestamps to verify sorting and filters.

---

## 5. Output Policy & Database Blueprint

Follow [`references/output-policy.md`](../references/output-policy.md):

1. **Routine Summary (4–8 lines target in chat)**:
   - **Models & Relationships**: 1-sentence summary of updated models or tables.
   - **Target Database & Adapter**: Identified engine (PostgreSQL, SQLite, etc.) and ORM adapter used.
   - **Indexing & Lock Evidence**: Indexes added and target-DB specific lock characteristics noted.
   - **Migration Safety**: Rehearsal result against disposable database.
   - **Evidence & Files**: Paths to generated migrations and seed files.
2. **Intermediate Milestone**:
   `✓ [schema-craft]: Migrations defined & rehearsed for <engine> (<N> models, rcpt_id)`
