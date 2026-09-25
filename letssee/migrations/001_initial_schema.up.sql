-- PulseMesh Schema Migration 001 UP
-- Enforces: Foreign Key indexing, Check Constraints, Explicit Cascade Semantics, ISO-8601 Timestamps

PRAGMA foreign_keys = ON;

-- 1. Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL CHECK(length(name) > 0),
    plan TEXT NOT NULL CHECK(plan IN ('starter', 'pro', 'enterprise')),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'suspended', 'deprovisioned')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- 2. API Keys Table
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY NOT NULL,
    tenant_id TEXT NOT NULL,
    key_hash TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('agent', 'admin', 'auditor')),
    revoked INTEGER NOT NULL DEFAULT 0 CHECK(revoked IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Foreign Key Index on api_keys(tenant_id)
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

-- 3. Audit Events Table (High-Throughput Telemetry Target)
CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY NOT NULL,
    tenant_id TEXT NOT NULL,
    agent_id TEXT NOT NULL CHECK(length(agent_id) > 0),
    action TEXT NOT NULL CHECK(length(action) > 0),
    resource TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('allowed', 'denied', 'flagged')),
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Foreign Key & Composite Ingestion Query Indexes on audit_events
CREATE INDEX IF NOT EXISTS idx_audit_events_tenant_created ON audit_events(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_agent ON audit_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_status ON audit_events(status);

-- 4. Webhooks Table
CREATE TABLE IF NOT EXISTS webhooks (
    id TEXT PRIMARY KEY NOT NULL,
    tenant_id TEXT NOT NULL,
    url TEXT NOT NULL CHECK(length(url) > 7),
    secret TEXT NOT NULL,
    events TEXT NOT NULL DEFAULT '["*"]',
    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

-- Foreign Key Index on webhooks(tenant_id)
CREATE INDEX IF NOT EXISTS idx_webhooks_tenant_id ON webhooks(tenant_id);
