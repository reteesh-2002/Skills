set -o pipefail
test-command 2>&1 | tee evidence.log
codes=("${PIPESTATUS[@]}")
test_rc=${codes[0]}
capture_rc=${codes[1]}
if (( capture_rc != 0 )); then
  # Record partial evidence independently of the test outcome.
  exit 74
fi
exit "$test_rc"
