# Roadmap

Items extracted from the original `unifi-network-maps` roadmap that belong to this library.

## Security

### Race condition in cache file operations (HIGH)
In `adapters/unifi.py` -- window between `tmp_path.write_text()` and `tmp_path.replace()` allows file modification. Fix: use `os.O_EXCL`, set restrictive permissions immediately on temp file.

### Incomplete XSS protection in SVG output (MEDIUM)
In `render/svg.py` -- custom `_escape_text()` only escapes `&<>`; should use `html.escape()` for consistency.

### Unvalidated environment variable integers (LOW)
In `adapters/unifi.py` -- env vars (`UNIFI_CACHE_TTL_SECONDS`, `UNIFI_RETRY_ATTEMPTS`, etc.) use `.isdigit()` but no range validation. Fix: add reasonable bounds checks after conversion.

## Features

### UniFi 2D theme
Matching Ubiquiti's 2D visual style.

### Multi-row client layout
Clients placed across multiple rows instead of one horizontal row, to keep SVG more square.

### Cable/link labeling
Extend port label composition with optional cable-name mapping file; needs port metadata (`port_desc`, `port_overrides`).

## Inline UniFi client (unifi_api.py)

### Auth response: check HTTP status before parsing JSON
`_validate_auth_response` doesn't check `response.status_code`. If the controller returns HTTP 403 with JSON that happens to contain `"roles"`, auth would silently succeed. Unlikely from a real UniFi controller, but a defensive check would be cleaner.

### Pass request timeout to session calls
`_get()` and `_authenticate()` don't pass `timeout=` to `requests`. Hanging requests are only caught by the outer `_call_with_timeout` ThreadPoolExecutor wrapper in `unifi.py`. Passing timeout natively to `self._session.get()` / `self._session.post()` would give a cleaner abort path.

### Scope SSL warning suppression
`urllib3.disable_warnings()` is process-global. If multiple `UnifiClient` instances exist (some with `verify_ssl=True`, some `False`), warnings stay suppressed for all. Could use a `warnings.catch_warnings()` context or track whether suppression was already applied.

## UniFi adapter (unifi.py)

### Remove redundant serialization layer for devices
`_serialize_device_for_cache` was needed when the upstream returned `UnifiDevice` objects that had to be converted to dicts. Now the inline client always returns `list[dict]`, so this is purely a field-filtering/normalization step. Still useful to avoid caching the full raw response, but the `get_field`/`first_attr` indirection could be simplified to direct `dict.get()` calls.

### Extract generic `_cached_fetch` helper
`fetch_devices`, `fetch_clients`, and `fetch_networks` follow the exact same ~25-line pattern: resolve site, check cache, build closure, call `_connect_and_fetch`, fall back to stale cache, save to cache. The only differences are endpoint method, cache key prefix, and serializer. A generic helper could eliminate the triplication, though the current code is straightforward enough that the duplication is low-cost.

## Model layer

### edges.py: Replace mutable parameter passing with context dataclass
`_collect_lldp_links` takes 7 mutable parameters (port_map, poe_map, speed_map, vlan_map, raw_links, seen) and mutates them all as side effects while also returning a `set[str]`. Same pattern in `_collect_uplink_links`. Both `build_edges` and `build_port_map` duplicate their initialization of these structures (~9 identical lines). Refactoring: create `EdgeBuildContext` dataclass to hold mutable state, return context instead of mutating params, extract shared init into `_prepare_edge_context()`.

### topology_coerce.py: Extract flexible field accessor
`_port_info_from_entry` (47 lines) repeats the same dict-vs-object access pattern 10+ times. A `_get_field_flexible(entry, key1, key2)` helper would eliminate the duplication and cut the function roughly in half.

### topology_coerce.py: Fix falsy-value checks in uplink extraction
`_extract_uplink_fields` uses `or` for fallback field access: `value.get("uplink_mac") or value.get("uplink_device_mac")`. If the first key returns `""` or `0`, it falls through to the second key. Should use `is None` checks instead.

### Tighten type annotations across model layer
Several functions use `object` or `Any` where more specific types are possible:
- `_aggregation_group` returns `object | None`, should be `str | None`
- `DeviceSource = object` is too permissive
- `snapshot.py` uses `Any` for serialization input/output
- `diff.py` spec functions use `Any` return types inconsistently

## Render layer

### Orthogonal/isometric SVG duplication
`svg.py` (orthogonal) and `svg_isometric.py` share substantial structural overlap: both build an SVG document, lay out nodes, draw edges, add labels, and render WAN info. The isometric renderer re-implements much of this with coordinate transforms. Potential approaches:
- Extract a shared `SvgDocument` builder that both renderers use for boilerplate (XML structure, defs, stylesheet injection, viewBox calculation)
- Unify edge-rendering logic where the only difference is coordinate projection

### svg_layout.py: Large layout functions
`_layout_physical` and `_layout_grouped` are each 40-60 lines with nested loops and coordinate arithmetic. Breaking each into smaller steps (assign layers, compute positions, apply spacing) would improve testability.

### SVG render module test coverage
SVG render modules with no dedicated unit tests. While integration tests provide some coverage, the following would benefit from targeted tests:
- `svg_layout.py` - layout algorithm correctness
- `svg_edges.py` - edge path generation

## Test suite

### Split test_topology.py
At 1,000+ lines with 100+ test functions, `test_topology.py` covers 5+ distinct source modules (edges, topology_coerce, clients, helpers, wan). Should be split into focused test files matching the modules they test.

### Add unit tests for core untested modules
Highest-value targets for this repo:
- `model/ports.py`, `model/edges.py`, `model/helpers.py` -- core logic with no direct tests
- `render/svg_layout.py`, `render/svg_edges.py` -- algorithmic code
