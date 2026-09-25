-- PulseMesh Schema Migration 001 DOWN (Rollback)
-- Cleanly removes all created tables, indexes, and constraints in reverse dependency order

PRAGMA foreign_keys = ON;

DROP INDEX IF EXISTS idx_webhooks_tenant_id;
DROP TABLE IF EXISTS webhooks;

DROP INDEX IF EXISTS idx_audit_events_status;
DROP INDEX IF EXISTS idx_audit_events_agent;
DROP INDEX IF EXISTS idx_audit_events_tenant_created;
DROP TABLE IF EXISTS audit_events;

DROP INDEX IF EXISTS idx_api_keys_hash;
DROP INDEX IF EXISTS idx_api_keys_tenant_id;
DROP TABLE IF EXISTS api_keys;

DROP TABLE IF EXISTS tenants;
