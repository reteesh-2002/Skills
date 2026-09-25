# Antigravity runtime audit evidence

This bundle accompanies `Antigravity_12_Skill_Principal_Architecture_Audit.md`, dated 25 September 2026.

The recorded results apply to the uploaded `Skills.zip` whose SHA-256 is:

`337f0ff4d02c81cc931e3a960be1b5e36038495a83a615cf79b1b9701cfdfad2`

## What is included

- `source/`: original root skills/contracts and runtime/hook/test scripts, copied without editing their bytes.
- `source_inventory.json`: hashes and sizes of these source files.
- `probe_results.json`: 23 observed probes, including the bundled suite and four concurrent-write trials.
- `audit_probes.py`: the reproduction harness. Its source/output roots have been changed to portable bundle-relative locations; the experiments are unchanged.
- `scenarios.cjs`: deliberately defective, synthetic security and memory fixtures.
- `scenario_results.json`, `scenarios.stdout.log`, `scenarios.stderr.log`: captured scenario results and Node warning.
- `signal-process.log`: captured output from the interrupted proxy attempt.
- `SHA256SUMS.json`: hashes of the original evidence files in this directory, excluding this checksum file itself.

These are local experiments, not an installed Antigravity conformance run or a production benchmark. Successful execution of an adversarial probe can demonstrate a product failure; do not interpret the harness exit code as a release-safety certification.

## Reproduce the script probes

Requirements: Linux, Bash, Git, Python 3, and Node.js. The original recorded environment is embedded in `probe_results.json`.

From the extracted bundle root:

```bash
python3 evidence/audit_probes.py
```

The harness uses `evidence/source/`, makes temporary Git repositories, runs local tests, and writes new results to `evidence/rerun/`. It makes no push/publish calls and does not use the imported archive's Git history. It injects sink failure with a temporary fake `tee`, rather than exhausting a real disk. It kills only the process group created for the signal fixture. Cleanup tests intentionally destroy only work created inside their temporary fixture checkout.

Optional explicit input/output paths:

```bash
python3 evidence/audit_probes.py evidence/source /tmp/agy-audit-new-results
```

Use a fresh output directory. The harness does not update the original recorded result file by default. Timing, generated IDs, and concurrent retained-entry counts can vary. The archived observations, not a later run, are the numbers reported in the audit.

## Reproduce the scenario fixtures

```bash
mkdir -p evidence/rerun
node --expose-gc evidence/scenarios.cjs evidence/rerun/scenario_results.json
```

The HTTP fixture uses two ephemeral loopback listeners and synthetic canaries. It never calls a real metadata endpoint or third-party server. It intentionally omits tenant authorization and URL egress validation to demonstrate why a mock-only oracle can be misleading.

The memory fixture allocates a stable baseline array, then begins retaining listeners/buffers after operation 8,000. It measures 10,000 synchronous operations, not an HTTP load test. It is intended to show that a five-percent heap threshold can pass despite a leak. Absolute memory values vary with runtime and platform; listener count and retained buffer growth are the principal discriminating measurements.

## Integrity check

From the extracted bundle root:

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib, json
root = Path('evidence')
for entry in json.loads((root / 'SHA256SUMS.json').read_text()):
    actual = hashlib.sha256((root / entry['path']).read_bytes()).hexdigest()
    assert actual == entry['sha256'], entry['path']
print('All recorded evidence checksums match.')
PY
```

Checksums provide integrity comparisons, not an independent authenticated signature. The report's proposed Zod, SQL, policy, and MCP interfaces are architectural examples; they are not represented as an implemented successor runtime.
