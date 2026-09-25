// PulseMesh System Configuration
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..');

export const config = {
  env: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '8443', 10),
  db: {
    path: process.env.DATABASE_PATH || path.join(REPO_ROOT, 'pulsemesh.db'),
    busyTimeout: 5000,
    journalMode: 'WAL',
    synchronous: 'NORMAL',
    foreignKeys: true,
  },
  ringBuffer: {
    capacity: 10000,
    flushIntervalMs: 50,
    flushBatchSize: 500,
  },
  security: {
    blockedSubnets: [
      '127.0.0.0/8',
      '169.254.0.0/16',
      '10.0.0.0/8',
      '172.16.0.0/12',
      '192.168.0.0/16',
      '::1/128',
      'fc00::/7'
    ]
  }
};
