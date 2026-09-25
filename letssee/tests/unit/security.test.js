// PulseMesh Security Verification Suite
// Exercises OWASP API Top 10: BOLA/IDOR, SSRF boundaries, and synthetic tenant isolation

import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { createServer } from '../../src/gateway/server.js';
import { SSRFProtector } from '../../src/gateway/ssrf.js';

test('Security & Boundary Verification Suite', async (t) => {
  const db = new DatabaseSync(':memory:');
  const app = createServer({ db });

  // Provision 2 isolated synthetic tenants
  db.prepare("INSERT INTO tenants (id, name, plan) VALUES ('tenant-a', 'Alpha Secure', 'enterprise')").run();
  db.prepare("INSERT INTO tenants (id, name, plan) VALUES ('tenant-b', 'Beta Secure', 'enterprise')").run();

  const keyA = 'sec_key_alpha_12345';
  const keyB = 'sec_key_beta_67890';
  const hashA = app.authEngine.hashKey(keyA);
  const hashB = app.authEngine.hashKey(keyB);

  db.prepare("INSERT INTO api_keys (id, tenant_id, key_hash, role) VALUES ('k-a', 'tenant-a', ?, 'agent')").run(hashA);
  db.prepare("INSERT INTO api_keys (id, tenant_id, key_hash, role) VALUES ('k-b', 'tenant-b', ?, 'agent')").run(hashB);

  // Seed private resource for Tenant A
  db.prepare(`
    INSERT INTO audit_events (id, tenant_id, agent_id, action, resource, status, metadata)
    VALUES ('evt-secret-a', 'tenant-a', 'agent-alpha', 'vault.unlock', 'res://keys/master', 'allowed', '{}')
  `).run();

  await t.test('1. BOLA / IDOR Defense: Cross-Tenant Access is strictly forbidden (403)', () => {
    // Tenant A querying its own event -> ALLOWED
    const authA = app.authEngine.authenticate(keyA);
    const allowRes = app.authEngine.authorizeResourceAccess(authA, 'audit_event', 'evt-secret-a');
    assert.equal(allowRes.authorized, true);

    // Tenant B attempting to access Tenant A's event -> FORBIDDEN (BOLA violation)
    const authB = app.authEngine.authenticate(keyB);
    const idorRes = app.authEngine.authorizeResourceAccess(authB, 'audit_event', 'evt-secret-a');
    assert.equal(idorRes.authorized, false);
    assert.equal(idorRes.status, 403);
    assert.equal(idorRes.error, 'BOLA_VIOLATION_CROSS_TENANT_ACCESS_DENIED');
  });

  await t.test('2. SSRF Protection: Loopback (127.0.0.1) and Localhost addresses blocked', () => {
    const loopback = SSRFProtector.validateWebhookUrl('http://127.0.0.1:8080/callback');
    assert.equal(loopback.allowed, false);
    assert.equal(loopback.reason, 'SSRF_BLOCKED_LOOPBACK');

    const localhost = SSRFProtector.validateWebhookUrl('http://localhost:3000/hook');
    assert.equal(localhost.allowed, false);
    assert.equal(localhost.reason, 'SSRF_BLOCKED_LOOPBACK');

    const ipv6Loopback = SSRFProtector.validateWebhookUrl('http://[::1]/internal');
    assert.equal(ipv6Loopback.allowed, false);
    assert.equal(ipv6Loopback.reason, 'SSRF_BLOCKED_LOOPBACK');
  });

  await t.test('3. SSRF Protection: Cloud Instance Metadata (169.254.169.254) blocked', () => {
    const metadata = SSRFProtector.validateWebhookUrl('http://169.254.169.254/latest/meta-data/');
    assert.equal(metadata.allowed, false);
    assert.equal(metadata.reason, 'SSRF_BLOCKED_METADATA');

    const gcpMeta = SSRFProtector.validateWebhookUrl('http://metadata.google.internal/computeMetadata/v1/');
    assert.equal(gcpMeta.allowed, false);
    assert.equal(gcpMeta.reason, 'SSRF_BLOCKED_METADATA');
  });

  await t.test('4. SSRF Protection: Private Subnets (10.x, 172.16.x, 192.168.x) blocked', () => {
    const rfc10 = SSRFProtector.validateWebhookUrl('http://10.0.0.5/api');
    assert.equal(rfc10.allowed, false);
    assert.equal(rfc10.reason, 'SSRF_BLOCKED_PRIVATE_IP');

    const rfc172 = SSRFProtector.validateWebhookUrl('http://172.20.1.1/hook');
    assert.equal(rfc172.allowed, false);
    assert.equal(rfc172.reason, 'SSRF_BLOCKED_PRIVATE_IP');

    const rfc192 = SSRFProtector.validateWebhookUrl('http://192.168.1.100:9000/notify');
    assert.equal(rfc192.allowed, false);
    assert.equal(rfc192.reason, 'SSRF_BLOCKED_PRIVATE_IP');
  });

  await t.test('5. SSRF Protection: Legitimate public URLs allowed', () => {
    const validPublic = SSRFProtector.validateWebhookUrl('https://api.github.com/webhook');
    assert.equal(validPublic.allowed, true);
    assert.equal(validPublic.url, 'https://api.github.com/webhook');

    const validHttps = SSRFProtector.validateWebhookUrl('https://hooks.slack.com/services/T00/B00/X00');
    assert.equal(validHttps.allowed, true);
  });

  await t.test('6. Authentication Invariants: Invalid and Revoked keys rejected', () => {
    // Unauthenticated / Missing key
    const missing = app.authEngine.authenticate('');
    assert.equal(missing.authenticated, false);
    assert.equal(missing.error, 'MISSING_API_KEY');

    // Invalid key
    const invalid = app.authEngine.authenticate('sec_bad_key');
    assert.equal(invalid.authenticated, false);
    assert.equal(invalid.error, 'INVALID_API_KEY');

    // Revoke key A and re-test
    db.prepare("UPDATE api_keys SET revoked = 1 WHERE id = 'k-a'").run();
    const revoked = app.authEngine.authenticate(keyA);
    assert.equal(revoked.authenticated, false);
    assert.equal(revoked.error, 'KEY_REVOKED');
  });
});
