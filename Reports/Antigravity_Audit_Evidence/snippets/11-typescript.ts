import { z } from 'zod';

const Count = z.number().int().nonnegative();
const Digest = z.string().regex(/^[a-f0-9]{64}$/);
const Counts = z.object({
  selected: Count, passed: Count, failed: Count,
  skipped: Count, expectedFailed: Count,
  unexpectedPassed: Count, cancelled: Count,
  flaky: Count
}).strict().superRefine((x, ctx) => {
  const terminal = x.passed + x.failed + x.skipped +
    x.expectedFailed + x.unexpectedPassed + x.cancelled;
  if (terminal !== x.selected || x.flaky > x.passed) {
    ctx.addIssue({ code: 'custom', message: 'Invalid outcome partition' });
  }
});

export const CheckReceipt = z.object({
  schemaVersion: z.literal('check.v1'),
  receiptId: z.string().uuid(),
  runId: z.string().uuid(),
  checkId: z.string().min(1).max(96),
  attempt: Count,
  leaseGeneration: Count,
  snapshotDigest: Digest,
  profileDigest: Digest,
  runnerVersion: z.string().min(1).max(64),
  execution: z.enum([
    'passed', 'failed', 'not_run', 'cancelled', 'timed_out', 'error'
  ]),
  exitCode: z.number().int().min(0).max(255).nullable(),
  signal: z.string().max(32).nullable(),
  evidence: z.enum(['complete', 'partial', 'missing', 'stale', 'invalid']),
  counts: Counts.nullable(),
  reportDigest: Digest.nullable(),
  logDigest: Digest.nullable(),
  warningIds: z.array(z.string().min(1).max(96)).max(1000)
}).strict();
