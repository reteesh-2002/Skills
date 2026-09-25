// PulseMesh SQLite WAL Client
import { DatabaseSync } from 'node:sqlite';
import { config } from '../config.js';

export function createDatabaseClient(dbPath = config.db.path) {
  const db = new DatabaseSync(dbPath);

  // Apply Idea Council architectural pragmas
  db.exec('PRAGMA foreign_keys = ON;');
  db.exec(`PRAGMA journal_mode = ${config.db.journalMode};`);
  db.exec(`PRAGMA synchronous = ${config.db.synchronous};`);
  db.exec(`PRAGMA busy_timeout = ${config.db.busyTimeout};`);

  return db;
}
