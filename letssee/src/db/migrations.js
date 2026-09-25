// PulseMesh Migration Runner
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const MIGRATIONS_DIR = path.resolve(__dirname, '../../migrations');

export function runMigrationsUp(db) {
  const upFile = path.join(MIGRATIONS_DIR, '001_initial_schema.up.sql');
  const sql = fs.readFileSync(upFile, 'utf-8');
  db.exec(sql);
}

export function runMigrationsDown(db) {
  const downFile = path.join(MIGRATIONS_DIR, '001_initial_schema.down.sql');
  const sql = fs.readFileSync(downFile, 'utf-8');
  db.exec(sql);
}
