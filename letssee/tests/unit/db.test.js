// Unit Tests for PulseMesh Database & Schema Invariants
import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { runMigrationsUp, runMigrationsDown } from '../../src/db/migrations.js';
import { seedEdgeCases } from '../../seeds/edge_cases.js';
import { TelemetryRingBuffer } from '../../src/db/ring-buffer.js';

test('Database Schema & Integrity Suite', async (t) => {
  const db = new DatabaseSync(':memory:');
  db.exec('PRAGMA foreign_keys = ON;');

  await t.test('1. Migration UP creates all tables and foreign key indexes', () => {
    runMigrationsUp(db);

    const tables = db.prepare(`
      SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
    `).all().map(r => r.name);

    assert.ok(tables.includes('tenants'), 'tenants table must exist');
    assert.ok(tables.includes('api_keys'), 'api_keys table must exist');
    assert.ok(tables.includes('audit_events'), 'audit_events table must exist');
    assert.ok(tables.includes('webhooks'), 'webhooks table must exist');

    const indexes = db.prepare(`
      SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;
    `).all().map(r => r.name);

    assert.ok(indexes.includes('idx_api_keys_tenant_id'), 'FK index on api_keys(tenant_id) must exist');
    assert.ok(indexes.includes('idx_audit_events_tenant_created'), 'Composite index on audit_events(tenant_id, created_at) must exist');
    assert.ok(indexes.includes('idx_webhooks_tenant_id'), 'FK index on webhooks(tenant_id) must exist');
  });

  await t.test('2. Check constraints reject invalid enumerations and empty strings', () => {
    // Invalid plan
    assert.throws(() => {
      db.prepare("INSERT INTO tenants (id, name, plan) VALUES ('bad', 'Bad Tenant', 'invalid_tier')").run();
    }, /CHECK constraint failed/);

    // Empty name
    assert.throws(() => {
      db.prepare("INSERT INTO tenants (id, name, plan) VALUES ('bad2', '', 'starter')").run();
    }, /CHECK constraint failed/);

    // Invalid role
    assert.throws(() => {
      db.prepare("INSERT INTO api_keys (id, tenant_id, key_hash, role) VALUES ('k1', 't-alpha', 'h1', 'superadmin')").run();
    }, /FOREIGN KEY constraint failed|CHECK constraint failed/);
  });

  await t.test('3. Foreign key constraints enforce relational integrity and cascade deletes', () => {
    // Cannot insert child with non-existent tenant
    assert.throws(() => {
      db.prepare("INSERT INTO api_keys (id, tenant_id, key_hash, role) VALUES ('k1', 'nonexistent', 'h1', 'agent')").run();
    }, /FOREIGN KEY constraint failed/);

    // Seed edge cases
    seedEdgeCases(db);

    const tenantCount = db.prepare('SELECT count(*) as count FROM tenants').get().count;
    assert.equal(tenantCount, 3, '3 edge case tenants should be seeded');

    // Delete tenant t-alpha and verify cascading deletion
    db.prepare("DELETE FROM tenants WHERE id = 't-alpha'").run();

    const orphanKeys = db.prepare("SELECT count(*) as count FROM api_keys WHERE tenant_id = 't-alpha'").get().count;
    const orphanEvents = db.prepare("SELECT count(*) as count FROM audit_events WHERE tenant_id = 't-alpha'").get().count;
    const orphanHooks = db.prepare("SELECT count(*) as count FROM webhooks WHERE tenant_id = 't-alpha'").get().count;

    assert.equal(orphanKeys, 0, 'api_keys must cascade on delete');
    assert.equal(orphanEvents, 0, 'audit_events must cascade on delete');
    assert.equal(orphanHooks, 0, 'webhooks must cascade on delete');
  });

  await t.test('4. Unicode, null byte string safety, and timezone handling', () => {
    const row = db.prepare("SELECT * FROM audit_events WHERE id = 'evt-unicode'").get();
    assert.ok(row, 'Unicode audit event must be present');
    assert.equal(row.agent_id, 'エージェント-42');
    assert.equal(row.resource, 'res://モデル/推論');

    const meta = JSON.parse(row.metadata);
    assert.ok(meta.input.includes('⚡'));
    assert.ok(row.created_at.includes('+14:00'), 'Timezone offset must be preserved in ISO timestamp');
  });

  await t.test('5. Telemetry Ring-Buffer flushes batches and drains cleanly', () => {
    const ringBuffer = new TelemetryRingBuffer(db, {
      capacity: 1000,
      flushIntervalMs: 50,
      flushBatchSize: 10
    });

    for (let i = 0; i < 25; i++) {
      const enqueued = ringBuffer.enqueue({
        id: `buf-evt-${i}`,
        tenant_id: 't-unicode',
        agent_id: `agent-${i}`,
        action: 'batch_test',
        resource: 'system',
        status: 'allowed',
        metadata: { iter: i },
        created_at: new Date().toISOString()
      });
      assert.ok(enqueued, 'Event should be enqueued');
    }

    const flushed = ringBuffer.drainSync();
    assert.equal(ringBuffer.getStats().buffered, 0, 'Buffer should be completely empty after drain');

    const count = db.prepare("SELECT count(*) as count FROM audit_events WHERE action = 'batch_test'").get().count;
    assert.equal(count, 25, 'All 25 batched events must be stored in database');
  });

  await t.test('6. Migration DOWN cleanly rolls back schema', () => {
    runMigrationsDown(db);

    const tables = db.prepare(`
      SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
    `).all().map(r => r.name);

    assert.ok(!tables.includes('tenants'), 'tenants table must be dropped');
    assert.ok(!tables.includes('api_keys'), 'api_keys table must be dropped');
    assert.ok(!tables.includes('audit_events'), 'audit_events table must be dropped');
    assert.ok(!tables.includes('webhooks'), 'webhooks table must be dropped');
  });
});
