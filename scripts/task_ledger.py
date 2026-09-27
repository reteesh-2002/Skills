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

    def add_task(self, task_id, title, owner="Coordinator", depends_on=None, acceptance_id=None):
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
                "detail": "Ready to execute",
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            data["tasks"].append(new_task)
            return new_task, data
        return self._with_lock(_add)

    def update_task(self, task_id, status=None, detail=None, evidence_ref=None, owner=None):
        """Updates task state, detail, owner, or evidence link."""
        if status is not None and status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Valid: {VALID_STATUSES}")

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
            target["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return target, data
        return self._with_lock(_update)

    def get_task(self, task_id):
        """Retrieves a single task record."""
        data = self.load()
        for t in data.get("tasks", []):
            if t["id"] == task_id:
                return t
        return None

    def render_markdown(self):
        """Generates a clean GFM markdown table of live task progress."""
        data = self.load()
        tasks = data.get("tasks", [])
        total = len(tasks)
        done = sum(1 for t in tasks if t["status"] == "Done")
        failed = sum(1 for t in tasks if t["status"] == "Failed")
        running = sum(1 for t in tasks if t["status"] == "Running")
        blocked = sum(1 for t in tasks if t["status"] == "Blocked")

        lines = [
            f"### 📋 Live Task Flow: {data.get('plan_title', 'Sprint')}",
            f"**Progress**: {done} of {total} tasks complete | Running: {running} | Blocked: {blocked} | Failed: {failed}",
            "",
            "| ID | Task | State | Owner | Detail |",
            "| :---: | :--- | :---: | :---: | :--- |"
        ]

        for t in tasks:
            lines.append(f"| {t['id']} | {t['title']} | {t['status']} | {t['owner']} | {t.get('detail', '')} |")

        return "\n".join(lines)

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

    upd_p = sub.add_parser("update")
    upd_p.add_argument("--id", required=True, help="Task ID")
    upd_p.add_argument("--status", choices=VALID_STATUSES, default=None)
    upd_p.add_argument("--detail", default=None)
    upd_p.add_argument("--evidence", default=None)
    upd_p.add_argument("--owner", default=None)

    sub.add_parser("status")
    
    render_p = sub.add_parser("render")
    render_p.add_argument("--output", default=None, help="Output markdown file path")

    args = parser.parse_args()
    ledger = TaskLedger()

    if args.cmd == "init":
        ledger.init_ledger(args.title)
        print(f"✓ Initialized task ledger for plan: {args.title}")
    elif args.cmd == "add":
        t = ledger.add_task(args.id, args.title, args.owner, args.depends, args.acceptance)
        print(f"✓ Added task {t['id']}: {t['title']} ({t['owner']})")
    elif args.cmd == "update":
        t = ledger.update_task(args.id, args.status, args.detail, args.evidence, args.owner)
        print(f"✓ Updated task {t['id']} -> {t['status']}: {t['detail']}")
    elif args.cmd == "status":
        print(ledger.render_markdown())
    elif args.cmd == "render":
        md = ledger.render_markdown()
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"✓ Rendered live task markdown to {args.output}")
        else:
            print(md)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
