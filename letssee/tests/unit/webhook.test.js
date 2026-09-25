// Webhook Dispatcher Test Suite (Deep Debugger Test Target)
import test from 'node:test';
import assert from 'node:assert/strict';
import { WebhookDispatcher } from '../../src/gateway/webhook-dispatcher.js';

test('Webhook Dispatcher Reliability Suite', async (t) => {
  await t.test('1. Dispatches valid webhook successfully', async () => {
    const dispatcher = new WebhookDispatcher();
    const result = dispatcher.dispatch(
      { id: 'wh-1', url: 'https://example.com/ok', secret: 'sec-1' },
      { id: 'evt-1', action: 'agent.login' }
    );
    assert.ok(result.queued, 'Webhook should be queued');

    // Wait for in-flight drain
    await dispatcher.drain();
    assert.equal(dispatcher.deliveryHistory.length, 1);
    assert.equal(dispatcher.deliveryHistory[0].status, 'delivered');
  });

  await t.test('2. Failsafe handling of delivery errors without unhandled promise rejection', async () => {
    const dispatcher = new WebhookDispatcher();

    // Injected defect will throw unhandled rejection here!
    dispatcher.dispatch(
      { id: 'wh-err', url: 'https://example.com/trigger-error', secret: 'sec-err' },
      { id: 'evt-2', action: 'agent.error' }
    );

    await dispatcher.drain();

    assert.equal(dispatcher.deliveryHistory.length, 1, 'Delivery attempt should be recorded in history');
    assert.equal(dispatcher.deliveryHistory[0].status, 'failed', 'Status should be marked failed, not crashed');
    assert.equal(dispatcher.getInFlightCount(), 0, 'In-flight set must be cleared on failure');
  });

  await t.test('3. Concurrent dispatch race condition immunity', async () => {
    const dispatcher = new WebhookDispatcher();
    for (let i = 0; i < 20; i++) {
      dispatcher.dispatch(
        { id: `wh-${i}`, url: `https://example.com/endpoint-${i}`, secret: 'sec' },
        { id: `evt-${i}`, action: 'agent.event' }
      );
    }

    await dispatcher.drain();
    assert.equal(dispatcher.deliveryHistory.length, 20, 'All 20 concurrent webhooks must complete');
    assert.equal(dispatcher.getInFlightCount(), 0, 'All in-flight slots must be empty');
  });
});
