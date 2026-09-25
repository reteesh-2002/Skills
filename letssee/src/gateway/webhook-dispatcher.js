// PulseMesh Webhook Dispatcher
// Surgical Fix applied via Deep Debugger protocol

export class WebhookDispatcher {
  constructor(options = {}) {
    this.timeoutMs = options.timeoutMs || 3000;
    this.inFlightRequests = new Set();
    this.deliveryHistory = [];
    this.isDraining = false;
  }

  dispatch(webhook, event) {
    if (this.isDraining) {
      throw new Error('GATEWAY_DRAINING: Cannot accept new webhook dispatches');
    }

    const payload = {
      event,
      timestamp: new Date().toISOString(),
      webhook_id: webhook.id
    };

    const task = (async () => {
      // Yield to microtask queue so task is guaranteed to be registered in inFlightRequests
      await Promise.resolve();
      try {
        if (webhook.url.includes('trigger-error')) {
          this.deliveryHistory.push({
            webhookId: webhook.id,
            status: 'failed',
            error: `DISPATCH_FAILED: Webhook delivery failed for ${webhook.url}`,
            timestamp: payload.timestamp
          });
          return { success: false };
        }

        // Simulating async delivery latency
        await new Promise(resolve => setTimeout(resolve, 10));

        this.deliveryHistory.push({
          webhookId: webhook.id,
          status: 'delivered',
          timestamp: payload.timestamp
        });
        return { success: true };
      } catch (err) {
        this.deliveryHistory.push({
          webhookId: webhook.id,
          status: 'failed',
          error: err.message,
          timestamp: payload.timestamp
        });
        return { success: false };
      } finally {
        this.inFlightRequests.delete(task);
      }
    })();

    this.inFlightRequests.add(task);
    return { queued: true, deliveryTask: task };
  }

  async drain(timeoutMs = 5000) {
    this.isDraining = true;
    if (this.inFlightRequests.size === 0) return;

    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('DRAIN_TIMEOUT: In-flight webhooks failed to drain')), timeoutMs)
    );

    await Promise.race([
      Promise.allSettled(Array.from(this.inFlightRequests)),
      timeoutPromise
    ]);
  }

  getInFlightCount() {
    return this.inFlightRequests.size;
  }
}
