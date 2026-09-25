// PulseMesh Zero-Trust SSRF Protection Engine
// Rejects loopback, link-local metadata (AWS/Azure/GCP 169.254.x), and private IPv4/IPv6 ranges

import net from 'node:net';

export class SSRFProtector {
  static isPrivateOrReservedIP(ip) {
    if (!net.isIP(ip)) return false;

    // IPv4 checks
    if (net.isIPv4(ip)) {
      const parts = ip.split('.').map(Number);
      const [a, b] = parts;

      // 127.0.0.0/8 (Loopback)
      if (a === 127) return true;
      // 169.254.0.0/16 (Link-Local / Cloud Instance Metadata)
      if (a === 169 && b === 254) return true;
      // 10.0.0.0/8 (Private RFC 1918)
      if (a === 10) return true;
      // 172.16.0.0/12 (Private RFC 1918)
      if (a === 172 && b >= 16 && b <= 31) return true;
      // 192.168.0.0/16 (Private RFC 1918)
      if (a === 192 && b === 168) return true;
      // 0.0.0.0/8
      if (a === 0) return true;

      return false;
    }

    // IPv6 checks
    if (net.isIPv6(ip)) {
      const normalized = ip.toLowerCase();
      // ::1 (Loopback)
      if (normalized === '::1' || normalized === '0:0:0:0:0:0:0:1') return true;
      // fe80::/10 (Link-Local)
      if (normalized.startsWith('fe8') || normalized.startsWith('fe9') || normalized.startsWith('fea') || normalized.startsWith('feb')) return true;
      // fc00::/7 (Unique Local)
      if (normalized.startsWith('fc') || normalized.startsWith('fd')) return true;

      return false;
    }

    return false;
  }

  static validateWebhookUrl(urlString) {
    let url;
    try {
      url = new URL(urlString);
    } catch {
      return { allowed: false, reason: 'INVALID_URL_SYNTAX' };
    }

    // Must be HTTP or HTTPS
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      return { allowed: false, reason: 'DISALLOWED_PROTOCOL' };
    }

    const hostname = url.hostname.toLowerCase();

    // Direct localhost/loopback strings
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]') {
      return { allowed: false, reason: 'SSRF_BLOCKED_LOOPBACK' };
    }

    // Cloud metadata endpoints
    if (hostname === '169.254.169.254' || hostname === 'metadata.google.internal' || hostname.startsWith('169.254.')) {
      return { allowed: false, reason: 'SSRF_BLOCKED_METADATA' };
    }

    // Check if IP is private
    if (net.isIP(hostname) && this.isPrivateOrReservedIP(hostname)) {
      return { allowed: false, reason: 'SSRF_BLOCKED_PRIVATE_IP' };
    }

    return { allowed: true, url: url.toString() };
  }
}
