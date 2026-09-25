#!/usr/bin/env bash
set -euo pipefail

# Read stdin JSON payload from hook runner
PAYLOAD=$(cat)

# Extract tool name and command line if present using python
python3 - "${PAYLOAD}" << 'PYEOF'
import sys, json

payload_str = sys.argv[1]
try:
    data = json.loads(payload_str)
except Exception:
    data = {}

tool_call = data.get("toolCall", {})
tool_name = tool_call.get("name", "")
args = tool_call.get("args", {})
cmd = args.get("CommandLine", "")

# If command is attempting a release/push, verify release gate
if "git push" in cmd or "gh pr create" in cmd or "npm publish" in cmd:
    # Here we can run verify-release-gate if needed
    pass

# Always output valid PreToolUse hook contract
output = {
    "decision": "allow"
}
print(json.dumps(output))
PYEOF
