---
name: docs-architect
description: Public documentation, viral developer README, OpenAPI 3.1 contract, and Architecture Decision Record (ADR) engine. Transforms internal vertical slice code and contracts into high-craft, anti-slop documentation, interactive API specifications, and frictionless developer quickstart guides.
---

# Docs Architect (Public Documentation, Viral README & OpenAPI Engine)

Bridge the gap between internal working code and external human adoption. Transforms raw codebases and vertical slice contracts into **high-craft, anti-slop public documentation**, interactive **OpenAPI 3.1 specifications**, and immutable **Architecture Decision Records (ADRs)**.

---

## 1. Activation and Boundaries

**Activation:**
- **Explicit Only**: Activates when explicitly requested via `/docs-architect`, `$docs-architect`, or when the user asks to write or polish a `README.md`, compile OpenAPI specs, create ADRs, or draft developer onboarding guides.
- Does not auto-activate during normal feature development or planning.

**Action Boundaries:**
- Generates and refines documentation artifacts (`README.md`, `openapi.yaml`, `docs/adr/*.md`, `docs/quickstart.md`).
- **Anti-Marketing-Slop Rule**: Never writes generic corporate fluff (*"cutting-edge AI-driven enterprise solution"*, *"seamlessly leverages power of"*). Every claim must be tied to a concrete benchmark, runnable command, or verified code capability.
- Does not modify application business logic or backend schemas.

---

## 2. The 4 Core Documentation Disciplines

Every documentation deliverable produced by `docs-architect` must adhere to these four disciplines:

### Discipline 1: The Viral, High-Craft README (`README.md`)
A great README converts a skeptical developer in under 15 seconds. Follow the layout in [`references/readme-template.md`](references/readme-template.md):
1. **The 5-Second Hook**: Single-sentence problem statement $\rightarrow$ concrete solution $\rightarrow$ key technical differentiator.
2. **1-Command Quickstart**: Exactly one command to clone, install, and run locally (e.g. `npx ...` or `docker compose up`).
3. **Mermaid Architecture Diagram**: Visual graph showing request flow through core primitives and vertical slices.
4. **Feature & Capability Matrix**: Crisp table of features with supported protocols and status.
5. **Environment Configuration Table**: Comprehensive table of every `.env` variable, its purpose, default value, and whether it is required.
6. **Contribution & Testing Guide**: Exact commands to run tests, linters, and verification gates.

### Discipline 2: OpenAPI 3.1 Specification from Vertical Slice Contracts
Generate or compile machine-readable OpenAPI 3.1 definitions from domain contracts:
- **Contract-to-Spec Ingestion**: Ingest Zod schemas (`modules/<slice>/contract.ts`) or Pydantic models and map them to OpenAPI components and endpoints.
- **Strict Typing**: Include parameter types, enum constraints, required fields, and realistic example payloads.
- **Error Response Definitions**: Document standard HTTP error shapes (`400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity`).
- **Interactive UI Integration**: Provide configuration snippets for embedding Scalar, Swagger UI, or Redoc in the app.
- See [`references/openapi-generator-guide.md`](references/openapi-generator-guide.md) for mapping patterns.

### Discipline 3: Architecture Decision Records (`docs/adr/`)
Capture consequential technical decisions as immutable records before tribal knowledge is lost:
- **Directory**: Store in `docs/adr/NNNN-title.md` (e.g. `docs/adr/0001-vertical-slice-architecture.md`).
- **Standard MADR Format**:
  1. **Status**: `Proposed` | `Accepted` | `Superseded by ADR-XXXX`.
  2. **Context & Problem Statement**: What technical challenge or trade-off triggered this decision?
  3. **Decision**: What choice was made, and what is the exact pattern?
  4. **Consequences**: Explicitly list positive outcomes, negative trade-offs, and compliance rules.
- See [`references/adr-template.md`](references/adr-template.md) for the authoritative format.

### Discipline 4: The 60-Second Developer Quickstart (`docs/quickstart.md`)
Zero-friction onboarding for new engineers or open-source contributors:
- **Prerequisites Verification**: Exact commands to check Node, Python, Docker, or tool versions.
- **Zero-Guesswork Setup**: Copying `.env.example`, running migrations, and seeding initial database records.
- **Sanity Verification Step**: The single command to run that proves the installation was successful (e.g. `curl http://localhost:3000/healthz`).

---

## 3. Output Format

When invoked, emit a structured **Documentation Package**:
1. **Artifact Preview**: Render the generated or updated file (`[NEW] README.md`, `[NEW] openapi.yaml`, or `[NEW] docs/adr/0001-*.md`).
2. **Anti-Slop Audit**: Confirm zero filler buzzwords and all commands verified against existing project manifests.
3. **Verification Command**: Runnable command to test doc links or lint OpenAPI syntax (e.g. `npx @redocly/cli lint openapi.yaml`).

---

## Reference Files

- [`references/readme-template.md`](references/readme-template.md) — High-density, battle-tested open-source and product README template.
- [`references/openapi-generator-guide.md`](references/openapi-generator-guide.md) — Guide for compiling vertical slice contracts into OpenAPI 3.1.
- [`references/adr-template.md`](references/adr-template.md) — Standardized Architecture Decision Record (ADR) template.
