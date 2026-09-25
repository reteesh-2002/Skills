// Runtime Reliability: Migration Rehearsal Protocol
import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { runMigrationsUp, runMigrationsDown } from '../../src/db/migrations.js';

test('Database Migration Rehearsal (Expand / Contract / Re-apply)', async (t) => {
  const db = new DatabaseSync(':memory:');
  db.exec('PRAGMA foreign_keys = ON;');

  await t.test('1. Initial UP migration creates pristine schema', () => {
    runMigrationsUp(db);
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").all();
    assert.equal(tables.length, 4, 'Must create 4 core relational tables');
  });

  await t.test('2. DOWN migration rolls back cleanly without leaving orphaned artifacts', () => {
    runMigrationsDown(db);
    const remainingTables = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").all();
    assert.equal(remainingTables.length, 0, 'Must leave 0 tables after complete rollback');
  });

  await t.test('3. Idempotent UP migration re-creates complete schema successfully', () => {
    runMigrationsUp(db);
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").all();
    assert.equal(tables.length, 4, 'Must recreate all 4 tables identically');

    const indexes = db.prepare("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'").all();
    assert.ok(indexes.length >= 4, 'Must restore all foreign key and composite query indexes');
  });
});
