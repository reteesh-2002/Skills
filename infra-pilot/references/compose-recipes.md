# Robust Docker Compose Stack Recipes

Production-aligned local development stacks with explicit health checks, conditional dependency boots, and persistent named volumes.

---

## 1. Full-Stack Production-Grade Local Dev (App + Postgres + Redis)

```yaml
services:
  # ──────────────────────────────────────────────
  # Primary Web Application
  # ──────────────────────────────────────────────
  app:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-app_dev}
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=debug
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app_network

  # ──────────────────────────────────────────────
  # Relational Database: PostgreSQL 16
  # ──────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-app_dev}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-app_dev}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 5s
    networks:
      - app_network

  # ──────────────────────────────────────────────
  # In-Memory Cache & Queue Broker: Redis 7
  # ──────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: ["redis-server", "--appendonly", "yes"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - app_network

networks:
  app_network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

---

## 2. Ingress & TLS Reverse Proxy: Caddyfile

When running behind Caddy for automatic local HTTPS certificates and reverse proxying:

```caddyfile
# Caddyfile
{
    email admin@example.com
}

localhost, app.localhost {
    reverse_proxy app:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
    }

    # Security headers (apply Strict-Transport-Security only on public production domains)
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        Content-Security-Policy "default-src 'self'"
    }

    request_body {
        max_size 10MB
    }

    encode gzip zstd
}
```
