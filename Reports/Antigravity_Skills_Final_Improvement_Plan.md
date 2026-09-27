**Antigravity Skills — Final Improvement Plan**

Prepared for Reteesh • 27 September 2026  
Status: implementation proposal; no repository changes have been made by this plan.

**1. Goal and scope**

Keep the existing skills suite and improve its reliability, review quality, token efficiency, and usability. The intended advantage over Superpowers is better results on your actual projects with fewer corrections and less wasted context. A claim of superiority must come from real evaluation.

The user experience should be simple: see live task progress, receive short updates, and open detailed evidence when needed. The engineering process behind that experience should remain inspectable.

This plan consolidates all agreed improvements:

- Repair verification, evidence validation, release detection, and TDD handling.
- Replace the simulated benchmark with real agent evaluation.
- Add independent code review and improve test quality.
- Choose solo or parallel execution based on the task.
- Make chat output concise and show task flow in supported sidebar/artifact views.
- Reduce repeated instructions, worker context, and model-facing logs.
- Strengthen specialist verification and recovery after interruptions.

The baseline is the reviewed Skills revision [098962a](https://github.com/reteesh-2002/Skills/commit/098962a144ccae638bae29c5246f276aa1dbb8cf). The comparison reference is Superpowers [8ca22db / v6.4.2](https://github.com/obra/superpowers/commit/8ca22dba9a94f28898bbce59f2537ff4d87c747d). Before implementation, inspect the current branch and map this plan onto any later changes. Do not overwrite newer fixes.

**2. What the review established**

The existing 21 runtime tests passed, but additional isolated probes exposed gaps. Passing the current suite is therefore a baseline, not the completion criterion.

| Finding at the reviewed revision | Required response |
|---|---|
| Release detection missed `git -C . push origin main` | Cover command options and documented invocation forms; clarify coverage boundaries |
| Conflicting receipt and manifest fields were accepted | Validate a complete shared evidence contract |
| A normal RED → fix → GREEN sequence on different commits was classified as a flaky retry | Separate test purpose and tested snapshot from retry history |
| A date-only waiver timestamp crashed without a valid hook response | Reject or normalize timestamps consistently and always return the documented response |
| Verification before committing could be rejected after the commit | Establish an explicit final verification step against the committed snapshot |
| Benchmark results were hard-coded | Remove empirical claims and implement real trials |
| Long execution output was streamed to the caller | Capture full logs on disk and emit compact, informative summaries |
| README specifies a 15–25-line foreground card | Replace it with the agreed concise output policy |

Preserve confirmed fixes, including failed-rescue worktree preservation, dirty-run evidence rejection, and empty-receipt rejection. Add regression coverage around those behaviors rather than rewriting working components without a reason.

**3. Delivery order**

| Release | Priority | Deliverables | Depends on |
|---|---|---|---|
| A — Reliable foundation | P0 | Evidence and release repairs, TDD semantics, real benchmark runner and baseline | Current revision review |
| B — Clear and reviewable work | P1 | Concise output, live task flow, independent review, better tests | Release A evidence contracts |
| C — Efficient execution | P2 | Adaptive orchestration, context reduction, durable recovery | Release B task state and review |
| D — Specialist validation | P2 | Tool-backed frontend, database, security and reliability checks; held-out comparison | Stable A–C workflow |

Build a thin benchmark runner early so later changes can be compared. Expand the task set after the core is stable. These releases are incremental; do not bundle every change into a single large rewrite.

**4. Release A: repair evidence and verification**

**A1. Establish one shared evidence contract**

Centralize parsing and validation used by the proxy, gate, and hook adapter. Retain the current entry-point scripts where practical; avoid maintaining independent copies of the same policy.

A verification record should identify:

- Schema version, run ID, check ID, and task ID where applicable.
- Purpose: expected RED test, verification, or retry.
- Exact tested commit/tree or explicitly identified development snapshot.
- Command arguments or command text plus shell, working directory, and relevant environment/dependency identity.
- Start/end times, exit code, runner identity, and parsed test counts.
- Raw-log location and digest, parser status, and warnings/skips.
- The prior run, if this is a retry.
- Any permitted exception, its scope, issuer, reason, and expiry.

Validate types, required fields, count consistency, and agreement between the manifest and referenced receipts. Unknown parser output must remain unknown; it must not become a green test count.

If semantics require a new schema version, provide an explicit migration or require fresh verification. Never silently reinterpret older records as stronger evidence.

A digest detects mismatches; it does not make agent-writable evidence independent or tamper-proof. Independently rerun release checks in CI.

**A2. Separate development checks from release evidence**

Support fast checks while editing, but label their source snapshot accurately. Those runs are useful feedback, not automatically release proof.

For final release verification:

1. Create the candidate commit.
2. Verify that commit in a clean, controlled checkout/worktree with the documented dependency setup.
3. Capture required checks and results.
4. Evaluate release readiness against the same candidate.
5. Invalidate affected evidence if the candidate or relevant verification configuration changes.

Define which generated files, fixtures, and environment inputs can affect execution. Do not assume a clean tracked tree alone describes every input.

Keep worktree rescue behavior safe: if preserving changes fails, stop cleanup and leave the work available.

**A3. Fix RED/GREEN and retry semantics**

An expected RED run proves that the selected test fails for the intended missing behavior. A syntax error, missing dependency, or broken runner does not prove that behavior.

GREEN must correspond to the intended test and changed implementation. Final regression verification remains a separate requirement.

Compare suspected flakiness only among comparable runs of the same source snapshot, command, and relevant environment. A new commit that fixes a failing test is normal development, not evidence of flakiness.

**A4. Repair release and hook handling**

Prefer structured command arguments when the host exposes them. Handle supported Git options and invocation forms explicitly. Do not treat a larger regular expression as a complete shell security boundary.

Document coverage for direct commands, shell command chains, and supported wrappers. Where arbitrary shell evaluation cannot be resolved safely, rely on the independent release/CI checks and state the local hook's limitation.

Every invocation must produce the host's documented response format, including errors. An evidence parser failure while evaluating a recognized release must not become permission to release. Ordinary unrelated commands must continue working.

For expiry values, adopt one explicit policy: require timezone-qualified timestamps and reject date-only values with a clear, valid response. Validate exception scope; never let the agent manufacture its own authorization.

**A5. Add behavioral regression cases**

| Acceptance ID | Scenario | Expected result |
|---|---|---|
| A-01 | Direct push without required evidence | Blocked |
| A-02 | Push with supported Git global options, including `-C` | Same policy as direct push |
| A-03 | Receipt disagrees with manifest about snapshot, command, or results | Blocked with the specific mismatch |
| A-04 | Missing, empty, truncated, or wrongly typed evidence | Valid error response; no false pass |
| A-05 | Date-only, invalid, expired, and valid timezone-qualified expiry | Deterministic policy and valid hook responses |
| A-06 | RED on one snapshot, fix, GREEN on another | Recorded as expected development |
| A-07 | Inconsistent results on the same comparable snapshot | Flagged for investigation as suspected flakiness |
| A-08 | Candidate changes after final verification | Previous evidence rejected as stale |
| A-09 | Zero tests or unrecognized test output | No invented successful test execution |
| A-10 | Rescue commit fails | Worktree and uncommitted files preserved |
| A-11 | Read-only command through the hook | Allowed normally |
| A-12 | Final candidate passes required checks | Readiness recorded for that candidate only |

Exercise actual scripts and real small test programs in temporary repositories. Do not perform real pushes or publish packages for these tests.

**5. Release A: replace the benchmark**

Rename or remove the current simulated report and label any retained mock fixture clearly. Existing hard-coded results must not appear in performance claims.

The real harness must:

- Invoke a real supported agent runner; do not silently substitute a simulation.
- Start from clean, equivalent task repositories.
- Pin the suite revision, model/version, settings, available tools, and budget.
- Compare the agent without either suite, Superpowers, and your suite.
- Let each suite use its own workflow within the same allowed capabilities and budget.
- Record raw transcripts, actual changes, test execution, and termination conditions.
- Score success with independent acceptance tests and predefined review criteria.
- Mark unsupported modes or unavailable telemetry explicitly.

Start with a small end-to-end smoke set, then expand to 12–20 representative tasks. Include bug fixes, normal features, frontend work, migrations, and coupled refactors. Add interruption/resume and misleading-test cases.

Repeat initial comparisons at least three times per task/configuration when budget allows. Treat small samples as exploratory. Keep separate held-out tasks for the final comparison and alternate run order to reduce time-dependent bias.

Record task success, regressions, false completion, interventions, elapsed time, and total model usage across the coordinator and every worker/reviewer. Record cached and uncached usage separately when available. Report cost only from supported usage and applicable pricing; never substitute characters divided by four for measured run usage.

Compare total effort and tokens per successful task, alongside failures and timeouts. A cheap failed run is not an efficiency improvement.

Acceptance:

- B-01: a real agent run produces a real change and independently evaluated result.
- B-02: an intentionally failing solution is scored as failure.
- B-03: all dispatched agents are included in usage accounting, or missing usage is disclosed.
- B-04: another run can reproduce the setup from the recorded configuration.
- B-05: claims identify the tasks, model, revisions, settings, sample size, and uncertainty.

**6. Release B: concise output and progressive detail**

Apply one output policy across the suite, including standalone skills. The coordinator owns the final user-facing summary in a multi-skill run.

| Surface | Default behavior |
|---|---|
| Chat during work | One short message at meaningful milestones, blockers, or decisions; respect the host's progress-update requirements |
| Final chat message | Usually 4–8 lines covering outcome, meaningful changes, verification, unresolved issues, and evidence location |
| Task view | Current work, dependencies, worker ownership, and real status |
| Evidence artifacts | Full logs, detailed findings, commands, counts, and traceable results |
| Detailed mode | Expanded explanation when requested or necessary to understand a consequential issue |

Support conversational requests such as “brief,” “normal,” and “show details.” These are output preferences; they are not assumed to be built-in slash commands.

The 4–8-line target is a default, not a truncation rule. Never hide failures, skipped checks, unavailable verification, unresolved material findings, or a decision needed from the user. Requested plans and documents can be complete artifacts with a short chat introduction.

Example final summary format:

- Outcome and the main change.
- Verification actually performed, with results.
- Any skipped check, blocker, or unresolved risk.
- Link/path to the relevant evidence.

Avoid repeating the complete plan, every command, all edited filenames, and separate completion cards from every skill.

For token efficiency, change the execution proxy so full stdout/stderr goes to a bounded-retention log file. Return a compact result with counts, significant failures/warnings, and a log location. On failure, include the relevant excerpt and retrieve more only when needed. Preserve redaction and avoid unnecessary copying of secrets into reports.

Acceptance:

- O-01: routine success produces one concise final summary.
- O-02: partial success names the unverified or failing part.
- O-03: requesting detail exposes the preserved evidence.
- O-04: workers do not each produce duplicate foreground summaries.
- O-05: compact mode reduces emitted model-facing log volume on a fixed fixture without losing the identified failure.
- O-06: summaries distinguish “implemented,” “verified,” and “released.”

**7. Release B: live task flow in the sidebar**

Use the host's supported task and artifact surfaces first. Antigravity documents task groups/progress sections and artifact views. Confirm the exact exposed controls in the installed version before implementation.

A skill can request and update supported artifacts; it cannot create arbitrary native sidebar widgets by instruction alone. If a dedicated sidebar widget needs an extension, treat that as a separate optional integration. The initial release must work through a maintained task artifact even without custom UI access.

Create one canonical task record per run. Suggested implementation: a versioned JSON record under the existing evidence/run directory, projected into the native task surface or a readable task artifact. Keep evidence receipts linked to it instead of duplicating their full contents.

Record:

- Stable task ID and short, user-readable title.
- Dependencies, owner/worker, status, and last update.
- Acceptance criteria IDs and relevant evidence references.
- Block reason or pending decision.
- Current run/worktree identity and revision where useful for resuming.

The coordinator is the only writer of canonical shared state; workers send structured updates. Use atomic writes and a revision counter to prevent stale updates from overwriting newer state.

| State | Meaning |
|---|---|
| Pending | Waiting to start or for a dependency |
| Running | Implementation or investigation is active |
| Blocked | Cannot proceed; show the concrete reason |
| Verifying | Relevant checks or required review are running |
| Done | The task's declared completion conditions are satisfied |
| Failed | Attempt ended without meeting the conditions |
| Cancelled | Explicitly removed or stopped; retain the reason |

A resumed task can return from Blocked/Failed to Running. A completed task whose evidence becomes stale must reopen for affected work or verification.

For investigation-only tasks, completion means the stated investigation deliverable is met; do not invent code tests. For coding tasks, an implementation being written is not sufficient to mark it Done.

The view should show:

- A short task list, with the active task easy to find.
- Completed/active/blocked counts and visible scope changes.
- Worker assignments only while parallel execution is active.
- References to changed files and evidence where supported.
- Last update and uncertain/interrupted state after a disconnect.

Example proposed view, not a statement of work already completed:

| Task | State | Owner | Detail |
|---|---|---|---|
| Define acceptance cases | Done | Coordinator | Requirements recorded |
| Implement behavior | Running | Worker A | Owns the service module |
| Add interface integration | Pending | Worker B | Waiting for agreed API |
| Verify and review | Pending | Coordinator | Requires integrated changes |

Update the view on state changes, not every shell command. Use counts such as “3 of 5 tasks complete,” with cancelled tasks identified. Do not invent percentages, remaining time, worker activity, or buttons unsupported by the host.

Acceptance:

- T-01: multi-step work creates a visible task record.
- T-02: blockers and owner changes appear after their state update.
- T-03: a failed check prevents premature completion.
- T-04: interruption/resume reconciles state with actual files, commits, and evidence.
- T-05: concurrent worker results do not lose task updates.
- T-06: chat and the task view derive their status from the same record.
- T-07: absent native integration falls back to a task artifact with no claim of a custom sidebar.

**8. Release B: independent review and meaningful tests**

Add one focused `code-reviewer` skill. Keep it separate from the implementer's verification so review can identify omissions the implementation tests miss.

Reviewer input: task requirements, relevant global constraints, changed code/diff, necessary surrounding code, and actual verification evidence. Do not require the reviewer to reread the entire conversation.

Each finding must give a location, concrete failure scenario, impact, and a way to verify the concern. Assess correctness, regressions, integration, test blind spots, and applicable security/data risks. Separate optional style preferences from blockers.

Ordinary features receive one independent final review when a real reviewer tool is available. High-risk changes receive relevant specialist review; independent task reviews are useful where interfaces or substantial deliverables justify them. Trivial changes do not need ceremonial extra agents.

Start with one correction pass for ordinary findings. Stop repeated low-value review loops, but never label unresolved material defects complete because a budget was reached. Preserve them in the task state and final result. Lack of a subagent tool must be disclosed as a self-review limitation, not represented as independent review.

Update `qa-sentinel` and testing references:

- Ask which realistic bug each test would catch.
- Derive expected values independently of the implementation.
- Assert observable behavior and relevant side effects.
- Use real components where practical; mock external boundaries deliberately.
- Use targeted mutation checks for critical logic when they resolve a concrete risk.
- Distinguish required regression coverage from unrelated existing failures, and report both accurately.
- Avoid tests that only inspect exact source wording or exist solely to satisfy process.

Acceptance:

- R-01: a seeded meaningful defect is found in the review fixture.
- R-02: findings include reproducible scenarios and distinguish severity.
- R-03: no independent-review claim is made without a real reviewer.
- R-04: an agreed critical behavior has a test that fails under a representative defect.
- R-05: deferred material findings remain visible and affect completion/release policy.

**9. Release C: adaptive execution and efficient context**

Choose the execution mode from uncertainty, consequences, interfaces, ownership conflicts, and available tools. File count and line count can inform the choice but must not decide it alone.

| Task shape | Default strategy |
|---|---|
| Small, clear change | Solo execution and relevant verification |
| Ordinary feature | Solo implementation with independent final review |
| Independent deliverables | Parallel workers within the configured cap, followed by integration checks |
| Tightly coupled refactor | Sequence shared interfaces; parallelize only genuinely independent portions |
| High-impact auth/data/release change | Stronger relevant verification and specialist review |
| Explicitly requested idea evaluation | Existing manual Idea Council workflow |

Respect configured worker limits and user choices. More workers are not automatically better. Keep Idea Council manually invoked and retain its requested participant behavior; do not run it for routine implementation.

Before parallel work, define ownership, shared interfaces, acceptance criteria, and integration order. The coordinator owns shared state and resolves interface conflicts. Test the combined result after merging worker output.

Give each worker a concise brief containing the goal, permitted scope, relevant constraints/interfaces, and verification expectations. Load only the specialist references it needs. Preserve global constraints that apply to its work.

Keep skill entry points short, with stack examples and detailed techniques in on-demand references. Maintain one authoritative shared policy for evidence and output; avoid copying long versions into every skill. References must remain discoverable and actually loaded when required.

Use task and token budgets as monitoring/escalation controls. When usage is unavailable, show that explicitly. Budget exhaustion means partial/blocked work, not a fabricated success.

Acceptance:

- E-01: a small task does not spawn unnecessary workers.
- E-02: independent tasks can run concurrently within the configured cap.
- E-03: shared-file conflicts cause coordination, not silent overwrites.
- E-04: each worker receives the constraints needed for its task.
- E-05: integration checks run against the combined result.
- E-06: observed usage includes all workers and reviews where telemetry permits.

**10. Release C: durable recovery**

Persist decisions, acceptance criteria, task ownership, completed work, unresolved issues, and evidence references in the run ledger. Associate decisions with the relevant source revision and assumptions.

On resume:

1. Inspect the actual repository/worktree state.
2. Reconcile it with recorded task status and commits.
3. Mark interrupted workers as unknown until their status is confirmed.
4. Revalidate evidence affected by source or environment changes.
5. Continue the next valid task without redoing completed work unnecessarily.

Do not treat saved summaries as current truth when their assumptions changed. Keep temporary evidence and logs out of the code commit unless deliberately selected as documentation. Use bounded retention without deleting records needed by the active run.

Acceptance: an interrupted fixture resumes without duplicated implementation, lost uncommitted work, stale verification, or fabricated worker completion.

**11. Release D: strengthen specialist verification**

| Skill | Improvement | Evidence and acceptance |
|---|---|---|
| `frontend-artisan` | Respect existing design systems; verify responsive behavior, interaction and relevant accessibility | Real browser checks, required viewport screenshots, keyboard paths, loading/error/empty states; manual limitations disclosed |
| `schema-craft` | Choose indexes from query needs; plan compatible migrations and realistic recovery | Run migrations on a disposable representative database; validate data and affected queries; use forward recovery where reversal would be destructive |
| `security-verifier` | Focus on the changed trust boundaries and authorized test scope | Controlled account/tenant tests, reproducible authorization and isolation checks; no automatic production probing |
| `runtime-reliability` | Define workload, baseline and thresholds from project requirements | Comparable before/after measurements, relevant shutdown/timeout/backpressure checks, environment and sample size recorded |
| `deep-debugger` | Preserve hypothesis discipline and bounded investigation | Reproduction, cause, minimal fix, regression evidence; protect unrelated user edits during rollback |
| `ship-it` | Evaluate the full intended diff, final candidate, and actual authorization | Secret/release checks cover intended changes; readiness remains separate from permission to push or publish |

Avoid universal promises such as zero locks, always-reversible migrations, or fixed memory thresholds for every project. Demonstrate the behavior required by the specific project.

**12. File and responsibility map**

Paths below are current entry points or proposed additions. Confirm the actual layout before editing.

| File or area | Planned responsibility |
|---|---|
| `scripts/exec-proxy.sh` | Purpose-aware evidence, snapshot identity, concise command output |
| `scripts/verify-release-gate.sh` | Shared validation, release readiness, consistent error behavior |
| `.agents/hooks.json` and hook wrapper | Native hook schema, supported command extraction, delegate to canonical gate |
| Proposed shared runtime module | Evidence schema, parsing, validation and task-state helpers |
| `tests/verify_runtime.sh` and focused fixtures | Actual behavioral regression tests |
| `tests/benchmark_comparison.py` | Real runner adapters, evaluation and usage accounting |
| `Reports/benchmark_comparison_report.md` | Generated measured results; simulations clearly separated |
| `plan-master/SKILL.md` | Acceptance IDs, execution strategy, concise plan and task setup |
| `adaptive-worker-orchestrator-v2/` | Ownership, task updates, worker briefs, integration and recovery |
| Proposed `code-reviewer/SKILL.md` | Independent review contract and findings |
| `qa-sentinel/SKILL.md` | Meaningful tests, evidence rules, truthful completion |
| `ship-it/SKILL.md` | Final candidate verification and authorized release flow |
| Specialist skill references | Targeted tool-backed checks loaded when needed |
| `prompt-architect` and `anti-slop-spec` | Preserve lightweight routing/alias behavior |
| `README.md` and shared guidance | Updated output policy, installation/capabilities, limitations and measured claims |

Prefer shared helpers and reference files over adding a separate skill for every new runtime feature. Sidebar tracking belongs to orchestration and the host adapter; it does not need a separate mandatory skill invocation.

**13. Final acceptance and comparison**

Ship each release only when its behavioral checks pass and its limitations are accurately documented. For the combined suite, demonstrate:

- The release gate rejects stale and contradictory evidence in supported invocation paths.
- Expected RED/GREEN development succeeds without a false flaky classification.
- Task completion matches evidence and required review.
- Routine chat stays concise while material problems remain visible.
- Native task/artifact integration works on the supported host; the fallback works elsewhere.
- Parallel execution respects ownership and configured limits.
- Interrupted work resumes without losing or repeating work.
- The benchmark executes real agents and accounts for observed usage.
- Specialist claims are backed by relevant checks or explicitly marked unverified.

Predeclare the benchmark's primary outcome and acceptable tradeoffs. Aim for at least comparable held-out task success, fewer false completion/intervention events, and lower total tokens or elapsed time. Report distributions and failures, not only favorable averages.

If quality improves at a higher cost, describe that tradeoff. If gains appear only on frontend tasks, make that narrower claim. A small evaluation is evidence for those conditions, not proof that the suite is universally more powerful than Superpowers.

**14. Suggested implementation handoff**

Implement Release A first against the current repository. Confirm which reviewed defects still exist, preserve newer fixes, and keep compatibility with existing entry points where practical. Complete the regression cases and a real benchmark smoke run before expanding the workflow.

Then implement Release B with the native task/artifact capability available in the installed Antigravity version. Use one source of task status and one concise output policy across all skills. Add independent review without forcing extra agents on trivial work.

Proceed to Releases C and D using measured behavior to decide whether each added rule or helper earns its cost. Update the documentation and comparison report with actual results. Keep pushing, publishing, and destructive changes within the user's granted authorization.

**15. Source references**

The implementation should confirm host capabilities against current official documentation. These sources explain the comparison practices and available host surfaces; the design choices and acceptance criteria above are this plan's proposals.

- [Your reviewed Skills revision](https://github.com/reteesh-2002/Skills/tree/098962a144ccae638bae29c5246f276aa1dbb8cf)
- [Superpowers comparison revision](https://github.com/obra/superpowers/tree/8ca22dba9a94f28898bbce59f2537ff4d87c747d)
- [Superpowers: inline execution](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/executing-plans/SKILL.md)
- [Superpowers: subagent development and review](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/subagent-driven-development/SKILL.md)
- [Superpowers: writing good tests](https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/skills/test-driven-development/writing-good-tests.md)
- [Antigravity: task groups](https://www.antigravity.google/docs/tools/)
- [Antigravity: artifacts](https://antigravity.google/docs/artifacts)
- [Antigravity: artifact review](https://antigravity.google/docs/artifact-review)

