# Roadmap

Open work for `unifi-topology`, in rough priority order. Last reviewed against
3.3.0 on 2026-11-11; items from the original February 2026 roadmap that have
since shipped were removed (see `changelog.md`).

## 1. Correctness

### Isometric default layout can stack two nodes on one cell
A parent's position is the mean of its children's indices, so two switches
feeding one client can resolve to the same tile. 3.1.1 fixed this for
`iso_compact_layout=True` only and left the default tree layout "pending a
wider fix". To do: confirm it still reproduces on the default path, then fix
it there. This is the only open item that produces a wrong diagram.

## 2. Features

### Multi-row client layout (orthogonal)
Place clients across multiple rows instead of one horizontal row, to keep the
SVG closer to square. The isometric compact layout already does this; the
orthogonal renderer has no equivalent.

### Cable/link labeling
Extend port label composition with optional cable names. Needs port metadata
(`port_desc`, `port_overrides`). As a library this should accept a mapping
from the caller rather than read a mapping file itself; the format needs a
short design first.

## 3. Hardening

### Create the cache temp file owner-only
`_save_cache` (`adapters/_cache_store.py`) writes the temp file with the
default mode and then chmods it to 0600. The cache directory is already 0700
and checked, so exposure is small, but creating the file with
`os.open(..., O_CREAT | O_EXCL, 0o600)` removes the window entirely.

### Bound `UNIFI_CACHE_TTL_SECONDS`
The retry settings are clamped; the cache TTL accepts any non-negative
integer. Add an upper bound.

### Cache location (F50 remainder)
Relocating the default cache directory is user-facing and was deferred from
the July code review. Needs a migration note for downstream consumers.

## 4. Code quality

Do these opportunistically when touching the module in question.

### Edge discovery: finish the context refactor
`_collect_lldp_links` takes an `EdgeDiscoveryResult`, but
`_collect_uplink_links` (`model/_edge_discovery.py`) still takes `port_map`,
`raw_links` and `seen` as separate mutable parameters. Pass the result object
there too.

### Tighten type annotations in the model layer
- `_aggregation_group` returns `object | None`; should be narrower
- `DeviceSource = object` is too permissive
- `snapshot.py` uses `Any` for serialization input and output

### Orthogonal/isometric duplication
Partly addressed by `_svg_render_common`, `_svg_render_flow` and
`_svg_edge_shared`. Remaining: the shared edge-label recorder (F42 remainder,
`render/svg_edges.py` vs `render/_svg_iso_edge_labels.py`).

### Facade shims
- F37 remainder: `adapters/unifi.py` re-exports about 35 private names;
  removing them means rewriting the call sites in 14 test files
- F38 remainder: the `svg_layout` / `svg_iso_*` shim modules that only
  re-export private names

### Remaining code-review remainders
The partially done (`[~]`) findings in `code-review-2026-07.md`: F46 (conftest
factories), F48 (dead `_evict_client`), F52 (CI job dedup), F53/F56/F57
(heuristic tweaks such as WAN-speed bounds and `ap` substring classification,
cosmetic dead code), F55 (mock tests). That document is the source of truth
for what each one still lacks.

## 5. Tests

### Coverage check for `model/ports.py` and `render/svg_edges.py`
The original roadmap listed these as having no direct tests. Many focused test
files have been added since; run coverage and add targeted tests only where
these two modules are still thin.
