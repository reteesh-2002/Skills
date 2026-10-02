#!/usr/bin/env python3
"""
Antigravity Canonical Live Task Ledger
Atomic versioned task tracking and progress renderer across coordinator and worker subagents.
"""

import os
import sys
import json
import fcntl
import argparse
import datetime

VALID_STATUSES = ("Pending", "Running", "Blocked", "Verifying", "Done", "Failed", "Cancelled")

class TaskLedger:
    def __init__(self, ledger_path=None):
        if ledger_path is None:
            # Default to .evidence/tasks.json relative to repo root
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(script_dir, ".."))
            self.ledger_path = os.path.join(repo_root, ".evidence", "tasks.json")
        else:
            self.ledger_path = os.path.abspath(ledger_path)
        self.lock_path = self.ledger_path + ".lock"
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)

    def _with_lock(self, callback):
        """Executes callback under exclusive file lock with atomic temp file swap."""
        with open(self.lock_path, "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                data = self.load()
                result, updated_data = callback(data)
                if updated_data is not None:
                    updated_data["revision"] = updated_data.get("revision", 0) + 1
                    updated_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    tmp_file = self.ledger_path + ".tmp"
                    with open(tmp_file, "w", encoding="utf-8") as f:
                        json.dump(updated_data, f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(tmp_file, self.ledger_path)
                return result
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    def load(self):
        """Loads task ledger from disk, returning default structure if empty."""
        if not os.path.exists(self.ledger_path):
            return {
                "schema_version": "tasks.v1",
                "plan_title": "Active Execution Plan",
                "revision": 0,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "tasks": []
            }
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "schema_version": "tasks.v1",
                "plan_title": "Active Execution Plan",
                "revision": 0,
                "tasks": []
            }

    def init_ledger(self, plan_title):
        """Initializes a new task ledger for a plan."""
        def _init(data):
            new_data = {
                "schema_version": "tasks.v1",
                "plan_title": plan_title,
                "revision": 0,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "tasks": []
            }
            return True, new_data
        return self._with_lock(_init)

    def add_task(self, task_id, title, owner="Coordinator", depends_on=None, acceptance_id=None, block_reason=None, pending_decision=None):
        """Registers a new task."""
        if depends_on is None:
            depends_on = []

        def _add(data):
            for t in data["tasks"]:
                if t["id"] == task_id:
                    raise ValueError(f"Task '{task_id}' already exists.")
            new_task = {
                "id": task_id,
                "title": title,
                "owner": owner,
                "status": "Pending",
                "depends_on": depends_on,
                "acceptance_id": acceptance_id,
                "evidence_ref": None,
                "block_reason": block_reason,
                "pending_decision": pending_decision,
                "detail": "Ready to execute",
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            data["tasks"].append(new_task)
            return new_task, data
        return self._with_lock(_add)

    def update_task(self, task_id, status=None, detail=None, evidence_ref=None, owner=None, block_reason=None, pending_decision=None):
        """Updates task state, detail, owner, block reason, or evidence link."""
        if status is not None and status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Valid: {VALID_STATUSES}")

        # T-03: A failed check prevents premature completion
        if status == "Done" and evidence_ref:
            evidence_dir = os.path.dirname(self.ledger_path)
            rcpt_path = os.path.join(evidence_dir, "receipts", f"{evidence_ref}.json")
            if not os.path.exists(rcpt_path):
                raise ValueError(
                    f"Cannot mark task '{task_id}' Done: Physical receipt file not found at '{rcpt_path}'. "
                    f"Run verification via scripts/exec-proxy.sh first."
                )
            try:
                with open(rcpt_path, "r", encoding="utf-8") as rf:
                    rcpt_data = json.load(rf)
                exit_code = rcpt_data.get("exit_code", 0)
                failed_count = rcpt_data.get("metrics", {}).get("failed", 0)
                if exit_code != 0 or failed_count > 0:
                    raise ValueError(f"Cannot mark task '{task_id}' Done: Evidence '{evidence_ref}' recorded failure (exit code {exit_code}, {failed_count} failed tests).")
            except (json.JSONDecodeError, OSError) as e:
                raise ValueError(
                    f"Cannot mark task '{task_id}' Done: Receipt '{evidence_ref}' is corrupt or unreadable: {e}"
                )

        def _update(data):
            target = None
            for t in data["tasks"]:
                if t["id"] == task_id:
                    target = t
                    break
            if target is None:
                raise ValueError(f"Task '{task_id}' not found.")

            if status is not None:
                target["status"] = status
            if detail is not None:
                target["detail"] = detail
            if evidence_ref is not None:
                target["evidence_ref"] = evidence_ref
            if owner is not None:
                target["owner"] = owner
            if block_reason is not None:
                target["block_reason"] = block_reason
            if pending_decision is not None:
                target["pending_decision"] = pending_decision
            target["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return target, data
        return self._with_lock(_update)

    def reconcile_interrupted_state(self, current_git_tree_sha=None):
        """
        T-04: Reconciles ledger state after interruption/resume against actual files,
        commits, and evidence receipts.
        - Re-queues interrupted in-flight tasks ('Running' / 'Verifying') to 'Pending'.
        - Checks completed tasks: if current tree differs from their verified tree, flags stale evidence.
        """
        evidence_dir = os.path.dirname(self.ledger_path)

        def _reconcile(data):
            reconciled = []
            for t in data.get("tasks", []):
                task_id = t["id"]
                current_status = t["status"]

                # In-flight tasks interrupted mid-run
                if current_status in ("Running", "Verifying"):
                    t["status"] = "Pending"
                    t["detail"] = "Interrupted: session was interrupted, re-queued for execution"
                    t["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    reconciled.append(f"{task_id} (Running/Verifying -> Pending)")

                # Completed tasks whose evidence may have become stale
                elif current_status == "Done" and current_git_tree_sha and t.get("evidence_ref"):
                    rcpt_path = os.path.join(evidence_dir, "receipts", f"{t['evidence_ref']}.json")
                    if os.path.exists(rcpt_path):
                        try:
                            with open(rcpt_path, "r", encoding="utf-8") as rf:
                                rcpt_data = json.load(rf)
                            rcpt_tree = rcpt_data.get("git_tree_sha")
                            if rcpt_tree and rcpt_tree != current_git_tree_sha:
                                t["status"] = "Pending"
                                t["detail"] = f"Stale evidence: tree changed ({rcpt_tree[:8]} -> {current_git_tree_sha[:8]}), re-verification required"
                                t["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                                reconciled.append(f"{task_id} (Done -> Pending due to stale tree)")
                        except (json.JSONDecodeError, OSError):
                            pass
            return reconciled, data

        return self._with_lock(_reconcile)

    def get_task(self, task_id):
        """Retrieves a single task record."""
        data = self.load()
        for t in data.get("tasks", []):
            if t["id"] == task_id:
                return t
        return None

    def render_summary(self):
        """
        T-06: Derives a concise 1-line progress summary for chat output policy.
        """
        data = self.load()
        tasks = data.get("tasks", [])
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "Done")
        failed = sum(1 for t in tasks if t["status"] == "Failed")
        running = sum(1 for t in tasks if t["status"] == "Running")
        blocked = sum(1 for t in tasks if t["status"] == "Blocked")
        cancelled = sum(1 for t in tasks if t["status"] == "Cancelled")
        
        parts = [f"{done} of {total} tasks complete"]
        if running > 0:
            parts.append(f"Running: {running}")
        if blocked > 0:
            parts.append(f"Blocked: {blocked}")
        if failed > 0:
            parts.append(f"Failed: {failed}")
        if cancelled > 0:
            parts.append(f"Cancelled: {cancelled}")

        return " | ".join(parts)

    def render_markdown(self):
        """Generates a clean GFM markdown table of live task progress (T-01, T-02)."""
        data = self.load()
        tasks = data.get("tasks", [])
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "Done")
        failed = sum(1 for t in tasks if t["status"] == "Failed")
        running = sum(1 for t in tasks if t["status"] == "Running")
        blocked = sum(1 for t in tasks if t["status"] == "Blocked")
        cancelled = sum(1 for t in tasks if t["status"] == "Cancelled")

        summary_line = self.render_summary()
        lines = [
            f"### 📋 Live Task Flow: {data.get('plan_title', 'Sprint')}",
            f"**Progress**: {summary_line}",
            "",
            "| ID | Task | State | Owner | Detail |",
            "| :---: | :--- | :---: | :---: | :--- |"
        ]

        for t in tasks:
            detail = t.get("detail", "")
            if t.get("block_reason") and t["status"] == "Blocked":
                detail = f"Blocked: {t['block_reason']}"
            elif t.get("pending_decision"):
                detail = f"Pending decision: {t['pending_decision']}"
            lines.append(f"| {t['id']} | {t['title']} | {t['status']} | {t['owner']} | {detail} |")

        return "\n".join(lines)

    def render_artifact(self, output_path=None):
        """
        T-07: Fallback to rendered task artifact file when native UI is absent.
        """
        md = self.render_markdown()
        if not output_path:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(script_dir, ".."))
            output_path = os.path.join(repo_root, "TASK_PROGRESS.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        return output_path

def main():
    parser = argparse.ArgumentParser(description="Antigravity Live Task Ledger CLI")
    sub = parser.add_subparsers(dest="cmd")

    init_p = sub.add_parser("init")
    init_p.add_argument("title", help="Plan or sprint title")

    add_p = sub.add_parser("add")
    add_p.add_argument("--id", required=True, help="Task ID (e.g. T1)")
    add_p.add_argument("--title", required=True, help="Task title")
    add_p.add_argument("--owner", default="Coordinator", help="Owner / Worker")
    add_p.add_argument("--depends", nargs="*", default=[], help="Dependency task IDs")
    add_p.add_argument("--acceptance", default=None, help="Acceptance ID")
    add_p.add_argument("--block-reason", default=None, help="Reason why blocked")
    add_p.add_argument("--pending-decision", default=None, help="Pending decision needed")

    upd_p = sub.add_parser("update")
    upd_p.add_argument("--id", required=True, help="Task ID")
    upd_p.add_argument("--status", choices=VALID_STATUSES, default=None)
    upd_p.add_argument("--detail", default=None)
    upd_p.add_argument("--evidence", default=None)
    upd_p.add_argument("--owner", default=None)
    upd_p.add_argument("--block-reason", default=None)
    upd_p.add_argument("--pending-decision", default=None)

    sub.add_parser("status")
    sub.add_parser("summary")

    recon_p = sub.add_parser("reconcile")
    recon_p.add_argument("--tree", default=None, help="Current git tree SHA")

    render_p = sub.add_parser("render")
    render_p.add_argument("--output", default=None, help="Output markdown file path")

    args = parser.parse_args()
    ledger = TaskLedger()

    if args.cmd == "init":
        ledger.init_ledger(args.title)
        print(f"✓ Initialized task ledger for plan: {args.title}")
    elif args.cmd == "add":
        t = ledger.add_task(args.id, args.title, args.owner, args.depends, args.acceptance, args.block_reason, args.pending_decision)
        print(f"✓ Added task {t['id']}: {t['title']} ({t['owner']})")
    elif args.cmd == "update":
        t = ledger.update_task(args.id, args.status, args.detail, args.evidence, args.owner, args.block_reason, args.pending_decision)
        print(f"✓ Updated task {t['id']} -> {t['status']}: {t['detail']}")
    elif args.cmd == "status":
        print(ledger.render_markdown())
    elif args.cmd == "summary":
        print(ledger.render_summary())
    elif args.cmd == "reconcile":
        changes = ledger.reconcile_interrupted_state(args.tree)
        print(f"✓ Reconciled {len(changes)} task(s): {', '.join(changes) if changes else 'no changes'}")
    elif args.cmd == "render":
        out = ledger.render_artifact(args.output)
        print(f"✓ Rendered live task markdown to {out}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
