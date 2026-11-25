# High-Craft Developer README Template

Use this template when `docs-architect` writes or restructures a project's `README.md`. Designed for maximum developer conversion, zero marketing slop, and instant clarity.

---

```markdown
# [Project Name]

> **[One-sentence tagline explaining exactly what the project does and the primary problem it solves]**

[![CI](https://github.com/[owner]/[repo]/actions/workflows/ci.yml/badge.svg)](https://github.com/[owner]/[repo]/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-[0.1.0]-green.svg)](package.json)

---

## ⚡ 60-Second Quickstart

Get up and running locally with a single command:

```bash
# 1. Clone repository
git clone https://github.com/[owner]/[repo].git
cd [repo]

# 2. Setup environment and dependencies
cp .env.example .env
npm install        # or: pip install -r requirements.txt

# 3. Boot application & dependencies
docker compose up -d

# 4. Verify system health
curl http://localhost:8000/healthz
```

---

## 🏗️ Architecture Overview

The codebase is structured around **Vertical Slice Architecture** to keep domain modules hermetically isolated:

```mermaid
graph TD
    Client["Client / Frontend"] --> Ingress["API Gateway / Routes"]
    Ingress --> Core["src/core (DB, Auth, Logger)"]
    Ingress --> ModA["modules/auth (contract.ts)"]
    Ingress --> ModB["modules/billing (contract.ts)"]
    Ingress --> ModC["modules/portfolio (contract.ts)"]
    ModA -.-> Core
    ModB -.-> Core
    ModC -.-> Core
```

- **`src/core/`**: Shared frozen database clients, session context, and logging.
- **`src/modules/<slice>/`**: Domain modules. Each contains its own `contract.ts`, `routes.ts`, `service.ts`, and colocated tests.
- **Cross-Slice Rule**: Slices communicate strictly via frozen `contract.ts` interfaces; direct internal imports are disallowed.

---

## ✨ Key Capabilities

| Capability | Technical Standard | Benefit |
|---|---|---|
| **Bounded Modules** | Enforced by lint / review | Eliminates AI prompt amnesia and cascading regressions |
| **Transactional Outbox** | PostgreSQL write-ahead events | Zero data loss during background worker restarts |
| **Row-Level Security (RLS)** | Tenant-scoped database queries | Guaranteed multi-tenant data isolation at the DB level |
| **Idempotent Mutations** | `Idempotency-Key` header support | Prevents duplicate billing and operations on network retries |

---

## ⚙️ Environment Configuration

| Variable | Description | Default | Required |
|---|---|---|:---:|
| `PORT` | HTTP port the server binds to | `8000` | No |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` | **Yes** |
| `REDIS_URL` | In-memory cache and queue broker | `redis://localhost:6379/0` | No |
| `LOG_LEVEL` | Structured logging verbosity (`debug`, `info`, `warn`) | `info` | No |

---

## 🧪 Testing & Verification

Run the test suite and architectural boundary linters:

```bash
# Run unit & integration tests
npm test

# Run lint & typechecks
npm run lint
```

---

## 📄 License

Licensed under the [MIT License](LICENSE).
```
