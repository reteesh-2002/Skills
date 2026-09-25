// Runtime Reliability: Graceful Drain & SIGTERM Termination Protocol
import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { createServer } from '../../src/gateway/server.js';

test('Graceful Drain & Zero-Loss Lifecycle Suite', async (t) => {
  const db = new DatabaseSync(':memory:');
  const app = createServer({ db });

  // Provision tenant
  db.prepare("INSERT INTO tenants (id, name, plan) VALUES ('t-drain', 'Drain Corp', 'enterprise')").run();

  await t.test('SIGTERM graceful drain flushes in-flight webhooks and buffered audit events without data loss', async () => {
    // 1. Enqueue 50 telemetry events into the ring-buffer without waiting for auto-flush
    for (let i = 0; i < 50; i++) {
      app.ringBuffer.enqueue({
        id: `drain-evt-${i}`,
        tenant_id: 't-drain',
        agent_id: 'agent-drain',
        action: 'system.drain_test',
        resource: 'res://node',
        status: 'allowed',
        metadata: { i },
        created_at: new Date().toISOString()
      });
    }

    // 2. Dispatch 5 in-flight webhooks
    for (let i = 0; i < 5; i++) {
      app.webhookDispatcher.dispatch(
        { id: `wh-drain-${i}`, url: `https://example.com/drain-${i}`, secret: 'sec' },
        { id: `evt-drain-${i}`, action: 'drain.test' }
      );
    }

    assert.ok(app.webhookDispatcher.getInFlightCount() > 0, 'In-flight webhooks should be actively processing');

    // 3. Trigger graceful termination (mirrors SIGTERM signal handler)
    await app.closeGracefully();

    // 4. Verify post-drain invariants
    assert.equal(app.webhookDispatcher.getInFlightCount(), 0, 'All in-flight webhooks must be drained to 0');
    assert.equal(app.ringBuffer.getStats().buffered, 0, 'Ring-buffer must be completely drained to 0');

    // 5. Verify all 50 events were safely committed to database
    const persistedEvents = db.prepare("SELECT count(*) as count FROM audit_events WHERE action = 'system.drain_test'").get().count;
    assert.equal(persistedEvents, 50, 'All 50 buffered events must be safely flushed to database during graceful drain');
  });
});
