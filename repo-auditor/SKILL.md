---
name: repo-auditor
description: Full-repository cold-start defect hunter. Finds silent exception swallowing, config-vs-code drift, untested modules, E2E isolation bugs, doc-vs-reality mismatches, and git/remote sync gaps using a strict Reproducer-or-Drop rule. Explicit only — not auto-activated.
---

# Repo Auditor (Cold-Start Defect & Parity Gate)

Run an objective, evidence-only audit of the entire repository—not just a recent `git diff`. Designed to catch the exact hidden defects that survive unit tests and get flagged in later reviews.

---

## 1. Non-Negotiable Audit Rules

1. **Explicit Only**: Activate only when explicitly invoked (`$repo-auditor`, `@repo-auditor`, `/repo-auditor`, or explicit full-repo audit request).
2. **Reproducer-or-Drop Rule**: Never report hypothetical risks, style preferences, or generic advice as bugs. Every finding **must** include `file:line`, the exact broken code/config, and a concrete failure scenario or command.
3. **No Arbitrary `/10` Scores**: Never output subjective numeric ratings (`7.8/10`). Report objective pass/fail counts and verified defect severity (`CRITICAL`, `WARNING`).
4. **Read-Only by Default**: Inspect, execute read-only probes (or isolated `/tmp` tests), and report findings. Do not edit repository files unless explicitly asked to fix them.

---

## 2. Swarm Execution Model (`/swarm` Default)

Always run `repo-auditor` using `swarm` (parallel read-only workers on the shared message board) when the host exposes the `swarm` tool:

1. **Title & Spawn Read-Only Workers (`workspace: "inherit"`)**:
   - Call `swarm{action:"title", title:"Repo Auditor: Cold-Start Audit"}`.
   - Split the 6 vectors across lean, non-overlapping workers (e.g., `code-exceptions` for Vectors 1–2, `coverage-e2e` for Vectors 3–4, `docs-git` for Vectors 5–6). Keep each worker read-only (`workspace: "inherit"`).
   - Every worker brief must enforce the **Reproducer-or-Drop Rule** (`file:line` + concrete reproducer, no `/10` scores) and instruct the worker to post `[done]` with findings to the board.
2. **Coordinate & Verify**:
   - Call `swarm_wait` until all workers post `[done]`, cross-check every reported `file:line` and reproducer, then kill finished workers (`swarm{action:"kill", name:...}`) before delivering the final report.
3. **Host Fallback**: If `swarm` is unavailable on the host, fall back to parallel read-only subagents (`invoke_subagent`) or sequential execution.

---

## 3. The 6-Vector Cold-Start Audit Protocol

Execute all 6 vectors across the whole repository:

### Vector 1: Silent Failure & Exception Swallowing
- Scan for `except Exception: pass`, bare `except:`, `|| true`, or swallowed `returncode` checks.
- Verify every `try/except` around `json.loads`, `int()`, `float()`, or file I/O cannot silently mask a schema or type bug (e.g., casting a `dict` to `int` and falling back to a hardcoded default).

### Vector 2: Config-vs-Code & Schema Drift
- Compare every config file (`*.json`, `*.yaml`, `.env.example`, CI workflows) against the code that reads it.
- Verify keys, types (scalar vs object/array), and limits in code actually match the config file—never assume a config value is used just because the key name appears in code.

### Vector 3: Coverage Blind Spots
- List every executable script/module and match it to its test files. Flag any script or critical module with **0 tests**.
- Check CLI flags (`--dry-run`, `--uninstall`, `--fix`, `--global`, `--json`) and error branches (malformed input, non-dict JSON, missing files, path traversal) for missing tests.

### Vector 4: E2E & Environment Isolation
- Execute install/build/CLI flows inside a clean `/tmp` directory (never only in the repo root).
- Verify relative links inside installed/copied files still resolve, nested CWDs work, and `--uninstall` / cleanup leaves zero leftovers and preserves post-install user edits.

### Vector 5: Doc-vs-Reality Parity
- Verify `README.md`, `CONTRIBUTING.md`, and `REQUIREMENTS.md` against actual measurements: test counts, skill/module counts, CLI flags, tool classifications, and relative Markdown links.

### Vector 6: Git & Remote Sync Hygiene
- Run `git status --short` and check local `HEAD` against `origin/main` (if remote exists) so untracked files, uncommitted edits, or unpushed commits are explicitly surfaced.

---

## 4. Output Format

Follow [`references/output-policy.md`](../references/output-policy.md):

1. **Audit Summary**:
   - **Checks Run**: Commands executed + exact counts (`passed/total`, exit codes).
   - **Verified Defects**: `N CRITICAL, M WARNING` (0 findings = clean pass).
   - **Git & Sync State**: Clean/dirty + ahead/behind remote.
2. **Findings List** *(omit if 0 defects)*:
   - `**[CRITICAL|WARNING]** <Title>` — `path/to/file:Lxx`
   - **Defect**: Exact mismatch or broken behavior.
   - **Reproducer**: Command, input, or execution path proving the failure.
   - **Fix**: Minimal surgical change + regression test to lock it in.
3. **Subjective / Design Notes** *(optional, max 3 bullets, clearly separated from verified bugs)*.
