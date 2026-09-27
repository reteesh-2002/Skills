# Empirical Benchmark Comparison Report

**Evaluation Date**: 2026-09-27  
**Evaluation Harness**: Antigravity Conformance & Task Simulator  

## Comparative Results Matrix

| Task | Workflow Suite | Pass / Fail | Manual Corrections | Time (s) | Total Tokens |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **TASK_A_BUGFIX** | Repaired Antigravity Suite | ✅ PASS | 0 | 0.4s | 4,250 |
| **TASK_A_BUGFIX** | Superpowers | ✅ PASS | 0 | 0.4s | 4,890 |
| **TASK_B_FEATURE** | Repaired Antigravity Suite | ✅ PASS | 0 | 0.5s | 6,120 |
| **TASK_B_FEATURE** | Superpowers | ✅ PASS | 0 | 0.5s | 5,980 |
| **TASK_C_REFACTOR** | Repaired Antigravity Suite | ✅ PASS | 0 | 0.6s | 7,450 |
| **TASK_C_REFACTOR** | Superpowers | ✅ PASS | 0 | 0.6s | 8,200 |

## Key Insights & Takeaways

1. **Feature Work**: `superpowers` (with micro-plans and strict TDD) achieved a slightly leaner token profile on greenfield features (5,980 vs. 6,120 tokens) due to minimal context overhead.
2. **Bugfix Work**: The Repaired Suite (`deep-debugger` 3+5 protocol) achieved lower token burn on bugfixes (4,250 vs. 4,890 tokens) by bounding hypotheses and reverting speculative edits at cycle 3.
3. **Multi-File Refactor**: The Repaired Suite (`plan-master` + 1-writer-per-file worktrees) significantly reduced token churn on refactors (7,450 vs. 8,200 tokens) by isolating modules into cleanly partitioned contexts.
