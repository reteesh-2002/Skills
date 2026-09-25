// Runtime Reliability: 10,000-Operation Memory Soak Test
import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { runMigrationsUp } from '../../src/db/migrations.js';
import { TelemetryRingBuffer } from '../../src/db/ring-buffer.js';

test('10,000-Operation Memory Soak & Heap Stability Suite', async (t) => {
  const db = new DatabaseSync(':memory:');
  runMigrationsUp(db);

  // Setup synthetic tenant
  db.prepare("INSERT INTO tenants (id, name, plan) VALUES ('soak-tenant', 'Soak Tenant', 'enterprise')").run();

  const ringBuffer = new TelemetryRingBuffer(db, {
    capacity: 2000,
    flushIntervalMs: 20,
    flushBatchSize: 200
  });

  const heapSnapshots = [];
  const TOTAL_OPERATIONS = 10000;
  const SAMPLE_INTERVAL = 2500;

  // Baseline heap
  if (global.gc) global.gc();
  heapSnapshots.push({
    step: 'start',
    heapUsedMB: process.memoryUsage().heapUsed / (1024 * 1024)
  });

  await t.test(`Execute ${TOTAL_OPERATIONS} telemetry operations under continuous WAL micro-batches`, () => {
    for (let i = 1; i <= TOTAL_OPERATIONS; i++) {
      const ok = ringBuffer.enqueue({
        id: `soak-evt-${i}`,
        tenant_id: 'soak-tenant',
        agent_id: `agent-soak-${i % 10}`,
        action: 'agent.telemetry_burst',
        resource: 'res://compute/task',
        status: 'allowed',
        metadata: { op: i, timestamp: Date.now() },
        created_at: new Date().toISOString()
      });

      assert.ok(ok, 'Buffer should successfully ingest event or flush to keep room');

      if (i % SAMPLE_INTERVAL === 0) {
        if (global.gc) global.gc();
        heapSnapshots.push({
          step: `${(i / TOTAL_OPERATIONS) * 100}%`,
          heapUsedMB: process.memoryUsage().heapUsed / (1024 * 1024)
        });
      }
    }

    // Drain remaining
    ringBuffer.drainSync();

    if (global.gc) global.gc();
    heapSnapshots.push({
      step: 'end_drained',
      heapUsedMB: process.memoryUsage().heapUsed / (1024 * 1024)
    });

    const storedCount = db.prepare('SELECT count(*) as count FROM audit_events').get().count;
    assert.equal(storedCount, TOTAL_OPERATIONS, 'All 10,000 operations must be persisted in database');

    const startMB = heapSnapshots[0].heapUsedMB;
    const endMB = heapSnapshots[heapSnapshots.length - 1].heapUsedMB;
    const deltaMB = endMB - startMB;

    // Validate memory resilience: Heap growth across 10,000 operations must be strictly bounded (< 35MB)
    assert.ok(deltaMB < 35, `Heap growth (${deltaMB.toFixed(2)}MB) must not indicate unbounded memory leak`);
  });
});
