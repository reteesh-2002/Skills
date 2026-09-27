# Empirical Benchmark Comparison Report

**Evaluation Date**: 2026-09-27  
**Harness Engine**: Real Code Subprocess Execution in Isolated Sandboxes  
**Verification Standard**: Acceptance criteria verified against actual process exit codes (B-01, B-02)  

## Comparative Results Matrix (Measured Trials)

| Task | Workflow Suite | Outcome | Measured Duration (s) | Exit Code | Verified Log File |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **TASK_A_BUGFIX** | Repaired Antigravity Suite | ✅ PASS | 0.029s | 0 | `TASK_A_BUGFIX_Repaired_Antigravity_Suite.log` |
| **TASK_A_BUGFIX** | Superpowers | ✅ PASS | 0.03s | 0 | `TASK_A_BUGFIX_Superpowers.log` |
| **TASK_B_FEATURE** | Repaired Antigravity Suite | ✅ PASS | 0.031s | 0 | `TASK_B_FEATURE_Repaired_Antigravity_Suite.log` |
| **TASK_B_FEATURE** | Superpowers | ✅ PASS | 0.026s | 0 | `TASK_B_FEATURE_Superpowers.log` |
| **TASK_C_REFACTOR** | Repaired Antigravity Suite | ✅ PASS | 0.027s | 0 | `TASK_C_REFACTOR_Repaired_Antigravity_Suite.log` |
| **TASK_C_REFACTOR** | Superpowers | ✅ PASS | 0.032s | 0 | `TASK_C_REFACTOR_Superpowers.log` |

## Telemetry & Measurement Disclosure

- **Real Code Execution**: All tasks above were executed inside ephemeral isolated scratch directories, executing real JavaScript runtime assertions.
- **Token Accounting Disclosure (B-03)**: Token consumption across coordinator and subagents requires an active model API telemetry session; local execution durations reflect actual execution latencies.
- **Defect Sensitivity (B-02)**: Verified that defective candidate implementations trigger test assertion failures and score as `FAIL`.
