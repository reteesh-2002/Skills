// PulseMesh Zero-Trust Gateway Server
import http from 'node:http';
import { createDatabaseClient } from '../db/client.js';
import { runMigrationsUp } from '../db/migrations.js';
import { TelemetryRingBuffer } from '../db/ring-buffer.js';
import { AuthorizationEngine } from './auth.js';
import { SSRFProtector } from './ssrf.js';
import { WebhookDispatcher } from './webhook-dispatcher.js';
import { config } from '../config.js';

export function createServer(options = {}) {
  const db = options.db || createDatabaseClient(options.dbPath || config.db.path);
  runMigrationsUp(db);

  const ringBuffer = options.ringBuffer || new TelemetryRingBuffer(db, options.ringBufferOptions);
  const authEngine = new AuthorizationEngine(db);
  const webhookDispatcher = options.webhookDispatcher || new WebhookDispatcher();

  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const method = req.method;

    // Helper: JSON response
    const sendJson = (status, payload) => {
      res.writeHead(status, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(payload));
    };

    // Health check
    if (url.pathname === '/healthz' && method === 'GET') {
      return sendJson(200, {
        status: 'UP',
        engine: 'sqlite-wal',
        ringBuffer: ringBuffer.getStats()
      });
    }

    // Auth extraction
    const authHeader = req.headers['authorization'] || '';
    const apiKey = authHeader.replace(/^Bearer\s+/i, '') || req.headers['x-api-key'] || '';
    const authContext = authEngine.authenticate(apiKey);

    // 1. Telemetry Ingest (POST /api/v1/telemetry)
    if (url.pathname === '/api/v1/telemetry' && method === 'POST') {
      if (!authContext.authenticated) {
        return sendJson(401, { error: authContext.error });
      }

      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        try {
          const data = JSON.parse(body || '{}');
          if (!data.action || !data.agent_id) {
            return sendJson(400, { error: 'INVALID_EVENT_PAYLOAD: action and agent_id required' });
          }

          const event = {
            id: data.id || `evt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            tenant_id: authContext.tenantId, // Force tenant isolation!
            agent_id: data.agent_id,
            action: data.action,
            resource: data.resource || 'default',
            status: data.status || 'allowed',
            metadata: data.metadata || null,
            created_at: data.created_at || new Date().toISOString()
          };

          const enqueued = ringBuffer.enqueue(event);
          if (!enqueued) {
            return sendJson(503, { error: 'BACKPRESSURE: Ring buffer capacity saturated' });
          }

          return sendJson(202, { status: 'ENQUEUED', eventId: event.id });
        } catch {
          return sendJson(400, { error: 'INVALID_JSON_BODY' });
        }
      });
      return;
    }

    // 2. Telemetry Query (GET /api/v1/telemetry/:id)
    if (url.pathname.startsWith('/api/v1/telemetry/') && method === 'GET') {
      const eventId = url.pathname.split('/').pop();
      const authz = authEngine.authorizeResourceAccess(authContext, 'audit_event', eventId);
      if (!authz.authorized) {
        return sendJson(authz.status, { error: authz.error, details: authz.details });
      }

      const row = db.prepare('SELECT * FROM audit_events WHERE id = ?').get(eventId);
      return sendJson(200, { event: row });
    }

    // 3. Webhook Registration (POST /api/v1/webhooks)
    if (url.pathname === '/api/v1/webhooks' && method === 'POST') {
      if (!authContext.authenticated) {
        return sendJson(401, { error: authContext.error });
      }

      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        try {
          const data = JSON.parse(body || '{}');
          const ssrfCheck = SSRFProtector.validateWebhookUrl(data.url || '');
          if (!ssrfCheck.allowed) {
            return sendJson(400, {
              error: 'SSRF_VALIDATION_FAILED',
              reason: ssrfCheck.reason,
              details: 'Disallowed webhook destination (private subnet or metadata service)'
            });
          }

          const webhookId = data.id || `wh_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
          db.prepare(`
            INSERT INTO webhooks (id, tenant_id, url, secret, events, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
          `).run(
            webhookId,
            authContext.tenantId,
            ssrfCheck.url,
            data.secret || 'whsec_auto',
            JSON.stringify(data.events || ['*']),
            1,
            new Date().toISOString()
          );

          return sendJson(201, { webhookId, status: 'REGISTERED' });
        } catch (err) {
          return sendJson(400, { error: 'DATABASE_ERROR', details: err.message });
        }
      });
      return;
    }

    // Not found
    return sendJson(404, { error: 'ROUTE_NOT_FOUND' });
  });

  // Graceful shutdown protocol
  const closeGracefully = async () => {
    // 1. Stop accepting new requests
    server.close();
    // 2. Drain in-flight webhooks
    await webhookDispatcher.drain();
    // 3. Synchronously flush ring-buffer to WAL database
    ringBuffer.drainSync();
  };

  return {
    server,
    db,
    ringBuffer,
    authEngine,
    webhookDispatcher,
    closeGracefully
  };
}
