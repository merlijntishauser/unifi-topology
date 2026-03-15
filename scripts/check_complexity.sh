#!/usr/bin/env bash
# Check that no function exceeds complexity threshold (default: 10)
# Usage: check_complexity.sh [max_complexity]

MAX_COMPLEXITY=${1:-10}
VENV="${VENV:-.venv/bin}"

# Find functions with complexity > threshold
if [ "$MAX_COMPLEXITY" -le 10 ]; then
    high_complexity=$($VENV/radon cc src/unifi_topology -s 2>&1 | grep -E " - C \(| - D \(| - E \(| - F \(" || true)
else
    high_complexity=$($VENV/radon cc src/unifi_topology -s 2>&1 | grep -E " - C \(1[1-9]\)| - C \(20\)| - D \(| - E \(| - F \(" || true)
fi

if [ -n "$high_complexity" ]; then
    echo "Functions with complexity > $MAX_COMPLEXITY found:"
    echo "$high_complexity"
    exit 1
fi

exit 0
