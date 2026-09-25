// PulseMesh Tenant Authorization & BOLA/IDOR Defense Engine
import crypto from 'node:crypto';

export class AuthorizationEngine {
  constructor(db) {
    this.db = db;

    this.findKeyStmt = this.db.prepare(`
      SELECT k.id, k.tenant_id, k.role, k.revoked, t.status as tenant_status
      FROM api_keys k
      JOIN tenants t ON k.tenant_id = t.id
      WHERE k.key_hash = ?
    `);

    this.checkEventOwnershipStmt = this.db.prepare(`
      SELECT tenant_id FROM audit_events WHERE id = ?
    `);

    this.checkWebhookOwnershipStmt = this.db.prepare(`
      SELECT tenant_id FROM webhooks WHERE id = ?
    `);
  }

  hashKey(rawKey) {
    return crypto.createHash('sha256').update(rawKey).digest('hex');
  }

  authenticate(rawKey) {
    if (!rawKey) {
      return { authenticated: false, error: 'MISSING_API_KEY' };
    }

    const keyHash = this.hashKey(rawKey);
    const record = this.findKeyStmt.get(keyHash);

    if (!record) {
      return { authenticated: false, error: 'INVALID_API_KEY' };
    }

    if (record.revoked === 1) {
      return { authenticated: false, error: 'KEY_REVOKED' };
    }

    if (record.tenant_status !== 'active') {
      return { authenticated: false, error: 'TENANT_NOT_ACTIVE' };
    }

    return {
      authenticated: true,
      tenantId: record.tenant_id,
      role: record.role,
      keyId: record.id
    };
  }

  // BOLA / IDOR Verification: Enforces that caller tenant matches resource tenant
  authorizeResourceAccess(authContext, resourceType, resourceId) {
    if (!authContext || !authContext.authenticated) {
      return { authorized: false, status: 401, error: 'UNAUTHENTICATED' };
    }

    let ownerRow;
    if (resourceType === 'audit_event') {
      ownerRow = this.checkEventOwnershipStmt.get(resourceId);
    } else if (resourceType === 'webhook') {
      ownerRow = this.checkWebhookOwnershipStmt.get(resourceId);
    } else {
      return { authorized: false, status: 400, error: 'UNKNOWN_RESOURCE_TYPE' };
    }

    if (!ownerRow) {
      return { authorized: false, status: 404, error: 'RESOURCE_NOT_FOUND' };
    }

    // IDOR Trap: Target resource belongs to a foreign tenant
    if (ownerRow.tenant_id !== authContext.tenantId) {
      return {
        authorized: false,
        status: 403,
        error: 'BOLA_VIOLATION_CROSS_TENANT_ACCESS_DENIED',
        details: `Tenant '${authContext.tenantId}' forbidden from accessing resource owned by '${ownerRow.tenant_id}'`
      };
    }

    return { authorized: true, tenantId: authContext.tenantId };
  }
}
