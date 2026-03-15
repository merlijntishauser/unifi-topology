#!/usr/bin/env bash
# Check that no function exceeds complexity threshold (default: 5)
# Usage: check_complexity.sh [max_complexity]

MAX_COMPLEXITY=${1:-5}
VENV="${VENV:-.venv/bin}"

# Find functions with complexity > threshold
if [ "$MAX_COMPLEXITY" -le 5 ]; then
    rating_pattern=" - B \(| - C \(| - D \(| - E \(| - F \("
elif [ "$MAX_COMPLEXITY" -le 10 ]; then
    rating_pattern=" - C \(| - D \(| - E \(| - F \("
else
    rating_pattern=" - C \(1[1-9]\)| - C \(20\)| - D \(| - E \(| - F \("
fi

high_complexity=$($VENV/radon cc src/unifi_topology -s 2>&1 | grep -E "$rating_pattern" || true)

if [ -n "$high_complexity" ]; then
    echo "Functions with complexity > $MAX_COMPLEXITY found:"
    echo "$high_complexity"
    exit 1
fi

exit 0
