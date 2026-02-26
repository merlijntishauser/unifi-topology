#!/usr/bin/env bash
# Bump version interactively, sync files, commit, tag, and push
set -e

current=$(python3 -c "
import re, sys
with open('pyproject.toml') as f:
    m = re.search(r'^version\s*=\s*\"(.+?)\"', f.read(), re.M)
    if m: print(m.group(1))
    else: sys.exit(1)
")

default=$(python3 -c "
import sys
v = sys.argv[1].strip().split('.')
if len(v) != 3 or not all(p.isdigit() for p in v):
    sys.exit(1)
major, minor, patch = map(int, v)
print(f'{major}.{minor}.{patch + 1}')
" "$current")

echo "Current version: $current"
read -p "New version [$default]: " next
next=${next:-$default}

if ! echo "$next" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "Invalid semver (expected x.y.z)"
    exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Working tree not clean. Commit or stash changes first."
    exit 1
fi

# Update pyproject.toml
sed -i '' "s/^version = \"$current\"/version = \"$next\"/" pyproject.toml

# Update __init__.py
sed -i '' "s/__version__ = \"$current\"/__version__ = \"$next\"/" src/unifi_topology/__init__.py

# Verify
if ! grep -q "version = \"$next\"" pyproject.toml; then
    echo "pyproject.toml version did not update"
    exit 1
fi
if ! grep -q "__version__ = \"$next\"" src/unifi_topology/__init__.py; then
    echo "__init__.py version did not update"
    exit 1
fi

git add pyproject.toml src/unifi_topology/__init__.py
git commit -m "Bump version to $next"
git tag -a "v$next" -m "v$next"
git push origin HEAD
git push origin "v$next"

echo "Version bumped to $next"
