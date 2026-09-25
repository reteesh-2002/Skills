// PulseMesh In-Memory Ring-Buffer for High-Throughput Telemetry
import { config } from '../config.js';

export class TelemetryRingBuffer {
  constructor(db, options = {}) {
    this.db = db;
    this.capacity = options.capacity || config.ringBuffer.capacity;
    this.flushIntervalMs = options.flushIntervalMs || config.ringBuffer.flushIntervalMs;
    this.flushBatchSize = options.flushBatchSize || config.ringBuffer.flushBatchSize;

    this.buffer = [];
    this.timer = null;
    this.totalEnqueued = 0;
    this.totalFlushed = 0;
    this.totalDropped = 0;

    // Prepared statement for fast batch insert
    this.insertStmt = this.db.prepare(`
      INSERT INTO audit_events (id, tenant_id, agent_id, action, resource, status, metadata, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    this.startTicker();
  }

  startTicker() {
    if (this.timer) return;
    this.timer = setInterval(() => {
      this.flush();
    }, this.flushIntervalMs);
    // Don't keep event loop alive if nothing else is running
    if (this.timer.unref) this.timer.unref();
  }

  stopTicker() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  enqueue(event) {
    if (this.buffer.length >= this.capacity) {
      this.totalDropped++;
      return false; // Backpressure drop
    }

    this.buffer.push(event);
    this.totalEnqueued++;

    if (this.buffer.length >= this.flushBatchSize) {
      this.flush();
    }
    return true;
  }

  flush() {
    if (this.buffer.length === 0) return 0;

    const countToFlush = Math.min(this.buffer.length, this.flushBatchSize);
    const batch = this.buffer.splice(0, countToFlush);

    this.db.exec('BEGIN IMMEDIATE;');
    try {
      for (const item of batch) {
        this.insertStmt.run(
          item.id,
          item.tenant_id,
          item.agent_id,
          item.action,
          item.resource,
          item.status,
          typeof item.metadata === 'object' ? JSON.stringify(item.metadata) : (item.metadata || null),
          item.created_at || new Date().toISOString()
        );
      }
      this.db.exec('COMMIT;');
      this.totalFlushed += batch.length;
      return batch.length;
    } catch (err) {
      this.db.exec('ROLLBACK;');
      // Put batch back to preserve data on failure
      this.buffer.unshift(...batch);
      throw err;
    }
  }

  drainSync() {
    this.stopTicker();
    let totalDrained = 0;
    while (this.buffer.length > 0) {
      totalDrained += this.flush();
    }
    return totalDrained;
  }

  getStats() {
    return {
      buffered: this.buffer.length,
      capacity: this.capacity,
      totalEnqueued: this.totalEnqueued,
      totalFlushed: this.totalFlushed,
      totalDropped: this.totalDropped,
    };
  }
}
