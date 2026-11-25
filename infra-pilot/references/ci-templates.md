# GitHub Actions CI/CD Pipeline Templates

Deterministic, fast, and secure CI/CD workflows integrating static checks, test execution, container builds, and release gates.

---

## 1. Full Production CI Pipeline (`.github/workflows/ci.yml`)

```yaml
name: Continuous Integration & Verification

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # ──────────────────────────────────────────────
  # Job 1: Static Analysis, Types & Boundary Linter
  # ──────────────────────────────────────────────
  lint-and-types:
    name: Lint, Typecheck & Slice Boundaries
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install Dependencies
        run: npm ci

      - name: TypeScript Compile
        run: npm run typecheck

      - name: Lint
        run: npm run lint

  # ──────────────────────────────────────────────
  # Job 2: Test Suite with Physical Evidence
  # ──────────────────────────────────────────────
  test-suite:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: app_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Environment
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install Dependencies
        run: npm ci

      - name: Run Test Suite
        env:
          DATABASE_URL: postgresql://postgres:testpassword@localhost:5432/app_test
        run: |
          npm test

  # ──────────────────────────────────────────────
  # Job 3: Docker Build Validation
  # ──────────────────────────────────────────────
  docker-build:
    name: Validate Container Build
    runs-on: ubuntu-latest
    needs: [lint-and-types, test-suite]
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker Image (Dry-Run / Cache Test)
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: app:ci-test
          cache-from: type=gha
          cache-to: type=gha,mode=max
```
