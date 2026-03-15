# Release Notes

## 1.2.1

Patch release focused on release hardening and maintainability. This release is intended to be a safe upgrade from `1.2.0` for downstream users.

### API Notes

- Public top-level exports remain unchanged.
- Public signatures for `build_topology`, `render_svg`, and `render_dual` remain unchanged.
- Serialized topology, snapshot, firewall, and inventory shapes remain unchanged.
- Internal modules were reorganized behind existing public re-exports; downstream imports from the documented API do not need to change.
- README and documentation examples now match the current stable API contract and are covered by tests.

### Quality Review

Release verification was run against the `1.2.1` tree with these commands:

```bash
ruff check .
pyright
pytest
xenon src/unifi_topology --max-absolute A --max-modules A --max-average A
./scripts/check_complexity.sh 5
```

Result:

- `ruff check .` passes
- `pyright` passes
- `pytest` passes with `911 passed, 2 skipped`
- `xenon` passes at `A/A/A`
- `./scripts/check_complexity.sh 5` passes

### Release Highlights

- Internal adapter, model, and render hotspots were decomposed without breaking the public library surface.
- API contract tests now protect the documented entry points and README-style usage.
- The test suite was normalized into focused modules, and every `tests/test_*.py` file is now `100` lines or fewer.
