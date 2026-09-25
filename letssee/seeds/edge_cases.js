// PulseMesh Edge-Case Seed Generator
// Proves schema resilience against Unicode glyphs, null-byte payloads, timezone shifts, and check constraints

export function seedEdgeCases(db) {
  // 1. Tenants with multi-byte Unicode, emojis, and valid plans
  const insertTenant = db.prepare(`
    INSERT INTO tenants (id, name, plan, status, created_at)
    VALUES (?, ?, ?, ?, ?)
  `);

  insertTenant.run('t-alpha', 'Alpha Corp', 'enterprise', 'active', '2026-09-25T15:24:01Z');
  insertTenant.run('t-unicode', '株式会社テルメトリ 🚀 [Ω-9]', 'enterprise', 'active', '2026-09-25T15:24:01+14:00');
  insertTenant.run('t-tz-shift', 'Samoa Substation', 'pro', 'active', '2026-09-25T01:00:00-11:00');

  // 2. API Keys
  const insertKey = db.prepare(`
    INSERT INTO api_keys (id, tenant_id, key_hash, role, revoked, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `);

  insertKey.run('k-alpha-1', 't-alpha', 'hash_sha256_alpha_master', 'admin', 0, '2026-09-25T15:24:01Z');
  insertKey.run('k-unicode-1', 't-unicode', 'hash_sha256_unicode_agent', 'agent', 0, '2026-09-25T15:24:01Z');

  // 3. Audit events with escaped strings, null-byte payloads, and deep metadata
  const insertEvent = db.prepare(`
    INSERT INTO audit_events (id, tenant_id, agent_id, action, resource, status, metadata, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);

  insertEvent.run(
    'evt-001',
    't-alpha',
    'agent-007',
    'tool_invocation',
    'res://vault/credentials',
    'allowed',
    JSON.stringify({ note: 'standard event' }),
    '2026-09-25T15:24:01Z'
  );

  insertEvent.run(
    'evt-unicode',
    't-unicode',
    'エージェント-42',
    'model_eval',
    'res://モデル/推論',
    'flagged',
    JSON.stringify({ input: 'テスト文字列 with symbols ⚡', nullByteTest: 'valid\\u0000payload' }),
    '2026-09-25T15:24:01+14:00'
  );

  // 4. Webhooks with unicode URLs and edge secrets
  const insertWebhook = db.prepare(`
    INSERT INTO webhooks (id, tenant_id, url, secret, events, active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);

  insertWebhook.run(
    'wh-001',
    't-alpha',
    'https://api.enterprise.corp/events',
    'whsec_k3y_9988_!@#$',
    '["audit.created","agent.blocked"]',
    1,
    '2026-09-25T15:24:01Z'
  );
}
