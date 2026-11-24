---
name: infra-pilot
description: Production containerization, Docker, compose, and CI/CD automation engine. Generates secure multi-stage non-root Dockerfiles, robust docker-compose development stacks, GitHub Actions CI pipelines, and zero-downtime healthcheck configurations. Use when containerizing an application, setting up local services (Postgres, Redis), configuring CI, or preparing production deployments.
---

# Infra Pilot (Production Containerization, Compose & CI/CD Engine)

Architect and implement production-grade containerization, local development infrastructure stacks, and automated continuous integration pipelines. Bridges the gap between verified local code and reliable production deployment.

---

## 1. Activation and Boundaries

**Activation:**
- **Explicit Only**: Activates when explicitly requested via `/infra-pilot`, `$infra-pilot`, or when the user asks to containerize the app, write a `Dockerfile`, create a `docker-compose.yml`, or configure CI/CD.
- Does not auto-activate during normal feature development or planning.

**Action Boundaries:**
- Generates infrastructure configuration files (`Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.github/workflows/ci.yml`, `Caddyfile`).
- **Never commits secrets or unencrypted credentials** into images or compose files; always uses environment variable interpolation (`${POSTGRES_PASSWORD}`).
- Does not run live production cloud deployments or manage production cloud clusters without explicit user authorization.

---

## 2. The 4 Production Infrastructure Invariants

Every infrastructure artifact produced by `infra-pilot` must adhere to these four engineering invariants:

### Invariant 1: Multi-Stage Non-Root Dockerfiles
- **Build vs. Runtime Separation**: Separate dependency compilation/bundling from the final runtime image to minimize attack surface and image size (target: distroless or alpine/slim bases).
- **Non-Root Execution**: Never run containers as root. Explicitly declare an unprivileged system user (e.g. `USER 10001:10001` or `USER node` / `USER appuser`).
- **PID 1 Signal Handling**: Use `tini`, `dumb-init`, or native runtime flags so that `SIGTERM` signals correctly reach application processes for graceful drain.
- **Layer Caching Optimization**: Copy dependency manifests (`package.json`, `pnpm-lock.yaml`, `requirements.txt`, `go.mod`) and install dependencies *before* copying application source code.
- **Mandatory `.dockerignore`**: Always generate a `.dockerignore` excluding `.git`, `node_modules`, `.env*`, `tests`, `coverage`, and temporary files.

### Invariant 2: Self-Healing Docker Compose Development Stacks
- **Explicit Health Checks**: Every database and service dependency (Postgres, Redis, MinIO) must define a concrete `healthcheck` (e.g. `pg_isready -U postgres`).
- **Startup Ordering with Conditions**: Application containers must declare `depends_on` with `condition: service_healthy` so the web app never boots before the database is accepting connections.
- **Named Persistent Volumes**: Persist state across container restarts using named volumes (`postgres_data:/var/lib/postgresql/data`).
- **Environment Parity**: Provide a companion `.env.example` file documenting all required configuration variables.

### Invariant 3: Deterministic GitHub Actions CI/CD Pipelines
- **Dependency Caching**: Cache package manager stores (`actions/cache` for npm/pnpm, pip, or go) to keep CI runtime fast.
- **Fail-Fast Parallelism**: Split verification into parallel jobs:
  1. `lint-and-types`: Static analysis and typechecks (TypeScript, Ruff/ESLint, or repo-configured linters).
  2. `test-suite`: Unit and integration tests with coverage reporting.
  3. `docker-build`: Container build validation with Buildx cache.
- **Deterministic Release Gate**: Verify clean git tree and test execution receipts before allowing release branches.

### Invariant 4: Zero-Downtime Healthcheck & Reverse Proxy Hygiene
- **Deep Healthcheck Endpoint**: Implement `GET /healthz` verifying database connectivity and queue health, alongside a shallow `GET /livez` for process liveness.
- **Caddy / Nginx Reverse Proxy**: Include a production Caddyfile or nginx config enforcing TLS, security headers (`X-Frame-Options`, `Content-Security-Policy`), request size limits, and gzip/zstd compression.

---

## 3. Standard Output Format

When generating infrastructure, produce a structured **Infrastructure Manifest**:
1. **Target Architecture Card**: Runtime stack, base image choice, and exposed ports.
2. **Configuration Files**: Complete, copy-pasteable files marked `[NEW]` (e.g. `[NEW] Dockerfile`, `[NEW] docker-compose.yml`).
3. **Local Validation Commands**: Exact commands to build, boot, and verify health:
   ```bash
   docker compose up -d --build
   docker compose ps
   curl -i http://localhost:8080/healthz
   ```
4. **Security & Production Checklist**: Non-root user confirmation, secret handling instructions, and backup procedures.

---

## Reference Files

- [`references/dockerfile-recipes.md`](references/dockerfile-recipes.md) — Production multi-stage Dockerfiles for Node/Next.js, Python/FastAPI, and Go.
- [`references/compose-recipes.md`](references/compose-recipes.md) — Robust docker-compose stacks with healthchecks and Postgres/Redis.
- [`references/ci-templates.md`](references/ci-templates.md) — GitHub Actions CI/CD workflows with test caching and container validation.
