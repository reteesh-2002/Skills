---
name: schema-craft
description: Database architecture, safe migrations, and type-safe API contract engine. Enforces production indexing strategies (foreign keys, compound queries), strict relational integrity (cascades, check constraints), zero-downtime migration protocols, and realistic edge-case seed data generation across PostgreSQL, SQLite, Prisma, Drizzle, and Django ORM. Use when designing data models, writing migrations, optimizing slow queries, or defining API contracts.
---

# Schema Craft

Production database architecture, safe migration engineering, and type-safe contract synchronization. Prevents silent performance cliffs, orphaned data, and breaking migration accidents in full-stack applications.

## The Production Database Invariants

When designing schemas or migrations, strictly enforce these 5 non-negotiable rules:

1. **Foreign Key Indexing Rule**: Every foreign key column MUST have an index. (PostgreSQL does *not* automatically index foreign keys; unindexed foreign keys cause table locks during deletes and 100x query slowdowns during joins).
2. **Explicit Delete Behavior**: Every relationship must specify explicit cascading semantics: `ON DELETE CASCADE`, `ON DELETE SET NULL`, or `ON DELETE RESTRICT`. Never leave it implicit.
3. **Timezone-Aware Timestamps**: Always use timezone-aware timestamps (`TIMESTAMPTZ` in Postgres, ISO-8601 strings in SQLite/Prisma). Never store local naive datetime.
4. **Safe Migration & Recovery Strategy**: For every schema modification, determine whether rollback is safe or if forward-recovery (expand/contract) is required to avoid data destruction. Rehearse migrations against a disposable representative database.
5. **Safe Column Addition**: Never add a `NOT NULL` column to an existing table without a `DEFAULT` value or a staged backfill protocol.
6. **Destructive Action Safety Gate**: Never run destructive DDL (`DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or `ALTER TABLE ... DROP COLUMN`) without explicit, unambiguous user confirmation. Always offer an archival or rename alternative first.

---

## The 4-Pillar Database Engineering Engine

### Pillar 1: Relational Architecture & Integrity
Design clean, normalized (3NF by default) data models:
- **Primary Keys**: Use `UUIDv7` or `ULID` for distributed/client-generated IDs; use standard `BIGINT IDENTITY` or auto-incrementing integers for internal sequential sequences.
- **Constraints**: Apply check constraints at the database level, not just in app code (e.g., `CHECK (price_cents >= 0)`, `CHECK (length(title) > 0)`).
- **Enums & State**: Use database enums or text check constraints for finite states (`status IN ('draft', 'published', 'archived')`) rather than magic integers.
- **Soft Deletes**: If soft deletion is required, use `deleted_at TIMESTAMPTZ NULL` with partial indexes (`WHERE deleted_at IS NULL`) so active queries stay lightning-fast.

### Pillar 2: Production Indexing Strategy
Index for actual query patterns, not wishful thinking:
- **Single-Column Indexes**: Foreign keys, high-cardinality search filters, and unique business keys (email, slug, username).
- **Composite Indexes**: Follow the **Equality, Range, Sort (ESR)** rule:
  - Put equality columns first: `tenant_id = '...'`
  - Put sort columns next: `ORDER BY created_at DESC`
  - Put range filters last: `score > 80`
  - Example: `CREATE INDEX idx_orders_tenant_date ON orders (tenant_id, created_at DESC);`
- **Zero Downtime Indexing**: In PostgreSQL, always specify `CREATE INDEX CONCURRENTLY` in production migrations to avoid locking table reads/writes.

### Pillar 3: Multi-ORM Support
Generate idiomatic, production-ready schemas across your active stack:

*   **Prisma (`schema.prisma`)**:
    ```prisma
    model User {
      id        String    @id @default(uuid())
      email     String    @unique
      posts     Post[]
      createdAt DateTime  @default(now()) @map("created_at")
      updatedAt DateTime  @updatedAt @map("updated_at")

      @@map("users")
    }

    model Post {
      id        String    @id @default(uuid())
      authorId  String    @map("author_id")
      author    User      @relation(fields: [authorId], references: [id], onDelete: Cascade)
      title     String    @db.VarChar(255)
      published Boolean   @default(false)
      createdAt DateTime  @default(now()) @map("created_at")

      @@index([authorId])
      @@index([published, createdAt(sort: Desc)])
      @@map("posts")
    }
    ```

*   **Drizzle ORM (`schema.ts`)**:
    ```typescript
    import { pgTable, uuid, varchar, boolean, timestamp, index } from 'drizzle-orm/pg-core';

    export const posts = pgTable('posts', {
      id: uuid('id').defaultRandom().primaryKey(),
      authorId: uuid('author_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
      title: varchar('title', { length: 255 }).notNull(),
      published: boolean('published').default(false).notNull(),
      createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
    }, (table) => ({
      authorIdx: index('idx_posts_author').on(table.authorId),
      publishedDateIdx: index('idx_posts_published_date').on(table.published, table.createdAt.desc()),
    }));
    ```

*   **Raw SQL / PostgreSQL**:
    ```sql
    CREATE TABLE users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email VARCHAR(255) NOT NULL UNIQUE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE posts (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      title VARCHAR(255) NOT NULL,
      published BOOLEAN NOT NULL DEFAULT false,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX idx_posts_author_id ON posts (author_id);
    CREATE INDEX idx_posts_published_created ON posts (published, created_at DESC);
    ```

### Pillar 4: Edge-Case Seed Data Generator
Never seed with 3 trivial records (`foo`, `bar`, `test`). Generate realistic edge-case seed scripts that probe:
1. **Unicode & Internationalization**: Accented names (`José Müller`), RTL text (`العربية`), Asian scripts (`东京`), emoji handles.
2. **Boundary Lengths**: Minimum allowable strings (1 char), maximum column lengths (255 chars, 5000 chars markdown).
3. **Data Volume**: At least 50–100 records across multiple relations to immediately surface pagination bugs, N+1 query leaks, and missing sort keys.
4. **Time Spread**: Records spanning multiple months, yesterday, 5 minutes ago, and future scheduled dates.

---

## Output Format: Database Architecture Blueprint (DAB)

When invoked, Schema Craft delivers:

```markdown
### 🗄️ Database Architecture Blueprint

#### 1. Entity-Relationship Overview
[Concise summary of models, relations (1:N, M:N), and ownership boundaries]

#### 2. Production Schema Definition
[The complete, annotated schema file: Prisma, Drizzle, SQL, or Django]

#### 3. Index & Performance Matrix
| Table | Index Name | Columns Indexed | Target Query Pattern |
| :--- | :--- | :--- | :--- |
| `posts` | `idx_posts_author` | `author_id` | Join optimization on author posts |
| `posts` | `idx_posts_feed` | `(published, created_at DESC)` | Public feed pagination |

#### 4. Reversible Migration Plan & Rehearsal
*   **Up Migration**: `ALTER TABLE ...` / `CREATE TABLE ...`
*   **Down Migration**: Safe rollback steps
*   **Rehearsal Probe**: Verify idempotency and rollback safety using `scripts/specialist_probes.py`:
    ```python
    from specialist_probes import rehearse_sqlite_migration
    res = rehearse_sqlite_migration(up_sql, down_sql, seed_sql, verify_query)
    assert res["passed"], "Migration rehearsal failed"
    ```
*   **Safety Audit**: Zero table locks, safe column additions verified

#### 5. Edge-Case Seed Generator
[Self-contained script or SQL insert fixtures with realistic boundary data]
```
