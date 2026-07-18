# Code Review Findings (2026-07-18)

Full-codebase review, five parallel reviewers (adapters/packaging, model core,
serialization/diff/mock, SVG render, text render/tests). Findings ordered by
priority. One commit per finding; checkbox ticked in the same commit as the fix.

Baseline at review time: ruff clean, pyright clean, 1110 tests passing.

Priorities:

- **P0** - critical: security or data exposure, fix immediately
- **P1** - major correctness bugs with concrete failure scenarios
- **P2** - structural refactorings (duplication, layering, decomposition)
- **P3** - minor bugs, dead code, hygiene (grouped by module into commit units)

## P0 - Critical

- [x] **F01 SVG attribute injection via `node_types` (verified XSS)** -
  `render/svg.py:231`, `render/_svg_iso_node_render.py:321`. `node_type` is
  interpolated raw into `fill="url(#node-{node_type})"`; a crafted type string
  produces a working `onload` handler in the emitted SVG (verified by
  execution). Fix: validate node type against the known type set, fall back to
  `other`. Also fixes: unknown types currently reference a nonexistent gradient
  and render an invisible node body (the iso fallback fill is dead code).
- [x] **F02 `node_data` attribute names injected unescaped** -
  `render/_svg_node_attrs.py:37`. Values are escaped, keys are not; a crafted
  key injects attributes (verified). Fix: validate keys against
  `^[A-Za-z_][\w-]*$`, skip invalid.
- [x] **F03 Control characters in group names produce unparseable SVG** -
  `render/svg_wan.py:36`, `render/_svg_iso_group_boundaries.py:108`. Both use
  `html.escape` instead of the project's `_escape_attr` (which strips
  XML-invalid chars); `groups={"bad\x01name": ...}` breaks the document
  (verified). Fix: use `_escape_attr`.
- [x] **F04 `Config.__repr__` leaks password and API key** -
  `adapters/config.py:43-50`. Plain dataclass fields appear in repr/str/
  tracebacks/pytest output. Fix: `field(repr=False)` on `password`, `api_key`.
- [x] **F05 No default HTTP timeout; `_call_with_timeout` cannot enforce one** -
  `adapters/_retry.py:35-55`, `adapters/unifi_api.py:164-165`. With the env var
  unset every request runs with `timeout=None` (hangs forever); the
  ThreadPoolExecutor wrapper blocks in `__exit__` until the hung call finishes
  anyway. Fix: finite default requests timeout (30s), env var overrides;
  remove the executor wrapper.

## P1 - Major correctness bugs

### Adapters

- [x] **F06 Retries hammer non-transient failures (account lockout risk)** -
  `adapters/unifi.py:139-153`. `_call_with_retries` retries bare `Exception`,
  including `UnifiAuthError` and 4xx, up to 20 times with backoff; repeated bad
  logins can lock the controller account. Fix: retry only transient errors
  (connection/timeout/5xx/429-aware).
- [x] **F07 Every fetch against a legacy controller performs a doomed UDM login
  first** - `adapters/unifi.py:212-233`. Failed-auth clients are never cached,
  so each `fetch_*` re-POSTs a failing `/api/auth/login` then falls back;
  `fetch_payload` triggers 3 failed logins - the exact pattern that trips
  UniFi's 429 rate limiting. Fix: memoize auth style per URL. Also chain or log
  the original UDM error when legacy fallback also fails (currently swallowed,
  `unifi.py:227-231`).
- [x] **F08 `invalidate_cache` silently cannot invalidate `devices` entries** -
  `adapters/unifi.py:114-136` vs `:277-286`. It omits `cache_key_extra`, but
  `fetch_devices` keys with `(str(detailed),)`; lookup misses, returns 0, no
  error. Fix: include the extra in the candidate paths.
- [x] **F09 `requests` exceptions leak through the `UnifiError` contract; rate
  limit detected by substring** - `adapters/unifi_api.py:150-166, 273-289`,
  `adapters/unifi.py:208-209`. Only login is wrapped; `fetch_devices()` against
  an unreachable host raises raw `requests.ConnectionError`. `_is_rate_limited`
  checks `"429" in str(exc)` (misfires on hosts/ports containing 429). Fix:
  wrap all HTTP calls into the `UnifiError` hierarchy carrying an HTTP status
  attribute; check the status, not the string.
- [x] **F10 Symlinked `.cache` in CWD makes every fetch raise, even with
  `use_cache=False`** - `adapters/_cache_store.py:22-31`, `_fetch.py:37`. The
  ValueError fallback re-runs the same failing call; `fetch_cached` builds the
  cache plan outside its try block. Fix: degrade to no-cache on cache-dir
  failure.
- [x] **F11 `swap_firewall_policy_order` is non-atomic** -
  `adapters/unifi_api.py:383-390`. If the second PUT fails, both policies hold
  the same index with no rollback. Fix: attempt rollback of the first PUT on
  failure; document partial-failure semantics.
- [x] **F12 `payload["data"]` never validated as a list** -
  `adapters/unifi_api.py:286-289, 42-43`. `{"data": null}` or a dict payload
  flows into model code as `Any`, failing far from the cause. Fix: isinstance
  check, raise `UnifiApiError` on shape mismatch.
- [x] **F13 PyPI publish not gated on CI** - `.github/workflows/publish.yml`.
  Tag push builds and publishes regardless of CI outcome. Fix: run the test
  suite in the publish workflow before build/upload.

### Model

- [x] **F14 `normalize_devices` is all-or-nothing; bare `int()` in LLDP
  coercion** - `model/lldp.py:24-27`, `model/_topology_device_coerce.py:119-141`.
  One LLDP entry with a non-numeric `local_port_idx`, or one device missing
  name/LLDP/uplink data, aborts normalization for the whole site. Fix: guard
  the int coercion; skip-and-log malformed devices.
- [x] **F15 WAN1 lookup substring-matches WAN2** - `model/wan.py:22-48`.
  `wan_id_lower in conf_id` means `"wan" in "wan2"`; WAN1 can resolve to the
  WAN2 port and both WanInfo slots point at the same physical port. Fix: exact
  match first, no bare substring.
- [x] **F16 MAC normalization inconsistent across edge discovery** -
  `model/_edge_discovery.py:116-127` vs `:44-50`, `model/helpers.py:76-77`.
  LLDP peer IDs are emitted raw (case-sensitive) while uplink IDs are
  normalized - third-party peers duplicate as two nodes. `normalize_mac` does
  not unify `-`/`:`/bare separators, so dash-format LLDP chassis IDs never
  match the device index. Fix: canonicalize separators in `normalize_mac`;
  normalize LLDP peer IDs.
- [x] **F17 `_client_is_wired` uses `bool()` on possibly-string field** -
  `model/_client_access.py:69-71`. `bool("false")` is True: wireless clients
  misclassified as wired, flipping mode filters and connection extraction. Fix:
  use `as_bool` like the rest of the codebase.

### Snapshot / diff

- [x] **F18 Round-trip drops `Device.in_gateway_mode`, flipping UX
  classification** - `model/snapshot.py:154-169, 290-307`. Not serialized nor
  restored; `_classify_ux_type` then reclassifies an AP-mode UX as a gateway
  after restore. Fix: serialize + restore; add a fields-introspection
  round-trip test that catches any future dropped field.
- [x] **F19 Snapshot `version` is write-only** - `model/topology.py:135,
  141-160`. Pre-2.0 name-keyed snapshots deserialize blindly and diff as
  everything-changed. Fix: validate version on load, raise on mismatch.
- [x] **F20 All edge events hardcode `entity_type="device"`** -
  `model/diff.py:493, 150-152`. Contradicts the documented contract;
  `filter(entity_types={"client"})` silently excludes client edges and the
  `client_edge_*` summary counts are dead code. Fix: classify edge entity type
  by endpoint.
- [x] **F21 Volatile wireless metrics cause diff churn** - `model/diff.py:
  193-205`. `signal`/`satisfaction` fluctuate every poll, emitting
  `client_node_changed` constantly. Fix: exclude volatile metrics from the
  compare set (consistent with `noise`/`tx_rate`/`rx_rate` already excluded).
- [x] **F22 Falsy `or`-coalescing breaks VLAN 0 / port 0** -
  `model/diff.py:181-190`. `client.get("vlan") or client.get("vlan_id")`
  falls through on legitimate 0. Fix: explicit `is None` chain.
- [x] **F23 Devices with empty MAC collide on diff key `""`** -
  `model/diff.py:467` vs `:443-445`. Two such devices collapse into one map
  slot and get compared against each other. Fix: return None key for falsy MAC
  like `_client_key` does, and skip.
- [x] **F24 Snapshot loaders crash on JSON `null` for list fields** -
  `model/snapshot.py:198, 360-361`. `"vlans": null` raises TypeError; every
  other loader type-guards. Fix: guard the three list fields.

### Renderers

- [x] **F25 LLDP/markdown port tables lost all connection and client data
  (v2 MAC-key regression)** - `render/lldp.py:196-216`,
  `render/_markdown_connections.py:14-34`. `build_port_map` returns MAC-keyed
  maps but lookups are by device name; connected devices and clients vanish
  from the rendered tables (verified end-to-end). Fix: key lookups by MAC,
  render client names; add an integration test feeding real
  `build_port_map`/`build_client_port_map` output into the renderers.
- [x] **F26 Mermaid `linkStyle` indices off by one when WAN is rendered** -
  `render/mermaid.py:139-157, 182-196, 279-296`. The WAN edge occupies link
  index 0 but edge styling still counts from 0, styling the wrong links
  (verified). Fix: offset indices by the number of pre-emitted edges; add a
  WAN+PoE test.
- [x] **F27 Mermaid crashes when the gateway is in no edge/group** -
  `render/mermaid.py:289-294`. `id_map[gateway_id]` raises KeyError (verified).
  Fix: `id_map.get`, skip WAN rendering when the gateway has no node.
- [x] **F28 Mermaid escaping uses backslash escapes Mermaid does not support** -
  `render/mermaid.py:13-16`. One `"` in a device name breaks the whole diagram;
  `\n` renders literally. Fix: `#quot;` and `<br/>`; update the golden tests
  that currently pin the broken output.
- [x] **F29 `render_device_inventory_table` performs no escaping** -
  `render/inventory.py:20-29`. A `|` in a device name misaligns the table. Fix:
  use `escape_markdown` and the shared `markdown_table_lines` helper. Also:
  `_markdown_connections.py:76-82` escapes multi-client `<li>` content with
  `html.escape` (does not escape `|`), inconsistent with the single-client
  path - use markdown escaping for both.
- [x] **F30 LLDP output duplicates the full Details table per device** -
  `render/lldp.py:271-286`, `render/markdown.py:91-99`. `_render_ports_section`
  embeds `render_device_port_details`, which prepends the Details table already
  rendered above (verified). Fix: render the port tables without the details
  block.
- [ ] **F31 Orthogonal VPN overlay box overlaps level-1 nodes** -
  `render/svg_vpn.py:98-99`, `render/_svg_render_flow.py:81-90`. Box is placed
  30px below the gateway (the tree root, at the top), covering the switches;
  reserved height is appended to the canvas bottom instead (verified). Fix:
  apply an offset like the WAN path (`apply_wan_offset`) does.
- [ ] **F32 Isometric floor grid not aligned with node tiles** -
  `render/_svg_iso_layout.py:79-87, 173-187, 215-225`. Grid lines translate by
  `(padding, padding)` while tiles translate by `(offset_x, offset_y)`; the
  delta is not a lattice vector (verified numerically). Fix: pass the node
  offsets into `_render_iso_grid`.

## P2 - Structural refactorings

- [ ] **F33 Symmetric generic snapshot deserialization** - `model/snapshot.py`.
  `to_dict` is generic (`_dataclass_to_dict`) but every `from_dict` is a
  hand-written field list - fields added later auto-serialize and silently drop
  on load (the F18 bug class). Replace with a `fields()`-introspection loader
  with scalar coercion; removes ~90 lines. Also fix: `client_from_dict`
  docstring claims validation it doesn't do; `_serialize_value` `str()`
  fallback is silently lossy; `_CLIENT_RELEVANT_KEYS` omits top-level
  `fw_version` (degrades inventory firmware after round-trip);
  `Topology.from_dict` should isinstance-guard list fields.
- [ ] **F34 Delete the parameter-injection layer in `_fetch.fetch_cached`** -
  `adapters/_fetch.py:97-119`. Ten module functions passed as parameters by the
  sole caller with the obvious implementations; keep only the
  `connect_and_fetch` seam. Removes ~40 lines of plumbing.
- [ ] **F35 Delete the callable-injection layer in `_svg_render_flow`** -
  `render/_svg_render_flow.py:101-193`. Eight `Callable` params, one caller,
  always the same bindings, no cycle avoided. Import directly; removes ~80
  lines and two indirection hops.
- [ ] **F36 Remove model compatibility facades re-exporting privates** -
  `model/topology_coerce.py`, `model/edges.py:25-72`, `model/classify.py`.
  ~50 underscore-private helpers re-exported in `__all__` in three different
  idioms; tests import them, freezing internals as de-facto API. Point tests at
  the real modules; export only public names.
- [ ] **F37 Remove adapter facades re-exporting privates** -
  `adapters/unifi.py:20-97`, `adapters/_cache.py`. ~35 private names in
  `__all__`, plus a line-for-line duplicated `_cache_lock` context manager
  (`unifi.py:99-111` vs `_cache_store.py:60-72`). Tests import from the real
  modules; delete the shims and the duplicate.
- [ ] **F38 Untangle render facade layering** - `render/svg_layout.py`,
  `render/svg_iso_nodes.py`, `render/svg_iso_edges.py`,
  `render/svg_isometric.py:15-66`, `render/_svg_iso_overlays.py`. Public-named
  modules are shims re-exporting only `_`-private names; cross-links route
  through odd places (`_svg_iso_group_boundaries` imports from `svg_wan`,
  `_svg_tree_layout` imports `_TYPE_ORDER` from `svg_icons`, a function-level
  import dodges a facade-created cycle). Fold or delete facades; move
  `_TYPE_ORDER` and `_vlan_group_colors` to neutral modules.
- [ ] **F39 Decompose `diff.py` (548 lines)** - `model/diff.py`. Split along
  existing seams: events/summary types, generic compare engine, describers +
  specs; `compare_topologies` stays as facade. Make `_build_summary`
  data-driven; extract the shared added/removed emission from
  `_compare_entities` (~48 lines).
- [ ] **F40 Extract shared overlay primitives (ortho/iso)** - overlay box
  metrics computed 4x (`svg_wan.py:55-66`, `svg_vpn.py:21-35, 162-167`,
  `_svg_iso_wan_overlay.py:24-44`) plus a fifth implicit hardcode
  (`_svg_render_flow.py:81`); globe drawing duplicated; centered-label loop
  appears 4x. One metrics helper, one globe fn, one label appender.
- [ ] **F41 Parameterize the VLAN striped-edge renderer** -
  `render/svg_edges.py:43-81` vs `render/_svg_iso_edge_draw.py:29-67`.
  Identical algorithm, differs only in constants; extract to
  `_svg_edge_shared.py`.
- [ ] **F42 Shared edge-label recorder and gateway-position helper** -
  `render/svg_edges.py:191-245` vs `render/_svg_iso_edge_labels.py:40-98`
  (identical control flow, ~60 lines); `_find_gateway_position` byte-identical
  in `svg_wan.py:187-195` and `_svg_iso_wan_overlay.py:179-186` (move to
  `_svg_render_common.py`).
- [ ] **F43 Consolidate the four int coercers** - `model/helpers.py:as_int`,
  `model/_topology_port_coerce.py:_as_int` (lets `True` through as VLAN 1),
  `model/_raw.py:_coerce_int` (drops float speeds), `_client_access.py:
  _parse_port_value`. One or two well-specified helpers in `helpers.py`;
  also de-duplicate the uplink double coercion
  (`_topology_device_coerce.py:58-74`) and the port table coerced twice per
  device (`:153-161` + `_topology_port_coerce.py:175-184`).
- [ ] **F44 Unify duplicated formatting across renderers** -
  `_format_wan_speed`/`_format_gbps` byte-identical in `render/mermaid.py:
  199-211` and `render/_svg_gateway_labels.py:8-17`; PoE predicates in 3
  places; device detail rows in 2 places with divergent model fallback (lldp
  drops `device.model`). Extract shared helpers; align the fallback chain.
- [ ] **F45 Typed client records** - `model/_topology_types.py:128`
  (`type DeviceSource = object`), `topology.py:125`
  (`clients: list[dict[str, object]]` + 3 type-ignores),
  `Device.network_table: list[dict[str, Any]]`. Introduce a TypedDict/Protocol
  for client records so pyright checks payload access; remove the ignores.
- [ ] **F46 Test-suite structure** - shared Device/PortInfo factories in
  conftest (9-kwarg `PortInfo` literal repeated ~25x in one file); move
  misplaced model tests out of `test_lldp_render.py:136-168`; fix
  `test_render_lldp_md_escapes_pipe_in_port_label` (tests nothing); register
  or drop the `acceptance` marker; add `--strict-markers`.

## P3 - Minor (grouped commit units)

- [ ] **F47 Rewrite AGENTS.md + README renderer docs** - version says 0.1.0
  (actual 2.2.2); complexity limit says 12 (CI enforces 5: ruff mccabe=5,
  xenon A, `check_complexity.sh 5`); "no Jinja2 templates" contradicts the
  runtime Jinja2 dependency and `render/templates/*.j2`; source layout omits
  ~40 modules (whole mermaid/markdown/lldp/vpn render family, firewall/
  device_stats/vpn model modules, adapter internals); README documents only
  SVG renderers though mermaid/lldp/inventory/legend are public API.
- [ ] **F48 Adapter minor cleanups** - dead `_evict_client`
  (`unifi.py:197-200`); `clear_client_cache()` after firewall writes discards
  all sessions for all configs (`unifi.py:424, 463`); lost exception chain in
  legacy fallback; module-level client cache not thread-safe (add a lock);
  `resolve_env_file` name check looser than its error message
  (`paths.py:136-137`); `--env-file` CLI-flavored error message and dead
  ImportError guard (`config.py:23-27`).
- [ ] **F49 `urllib3.disable_warnings` is process-global** -
  `adapters/unifi_api.py:133-136`. Constructing one `verify_ssl=False` client
  silences InsecureRequestWarning for the whole host process. Scope to the
  session (e.g. suppress via per-request warnings context or leave warnings
  on and document).
- [ ] **F50 Cache location and permissions** - `adapters/_cache_store.py:23`.
  Cache defaults to CWD under the predecessor project's name
  (`.cache/unifi_network_maps`); files contain MACs/IPs/hostnames and are
  world-readable. Prefer `~/.cache/unifi_topology`, write files 0600.
- [ ] **F51 Concurrent DNS lookups; surface bad `dns_server`** -
  `adapters/dns.py:33-41`. Sequential PTR queries with 2s lifetime each (100
  clients against a dead server = 200s); hostname-valued `dns_server` raises
  ValueError silently swallowed at debug level. Fan out with a thread pool;
  log the config error at warning.
- [ ] **F52 Packaging/CI hygiene** - exact-pinned build backend
  (`setuptools==83.0.0`, `wheel` unnecessary) breaks sdist installs if yanked;
  `push: ["**"]` + `pull_request` double-runs CI; 7 copy-pasted install blocks
  (composite action); fully serial job chain; ruff/pyright target 3.13 while
  floor is 3.12; public-surface inconsistencies (`fetch_payload` public but not
  exported, `clear_client_cache` exported from adapters but not top level).
- [ ] **F53 Model minor correctness group** - `_client_unifi_flag` first-flag
  short-circuit misclassifies (treat only True as decisive, check ucore first)
  (`_classify_client.py:121-129`); uplink `port_idx` fallback labels the wrong
  end of the link (`_topology_device_coerce.py:18-25`,
  `_edge_discovery.py:69`); reversed tree edges keep the stale label
  orientation (`edges.py:188-200`); VLAN-0 clients invisible in
  `build_vlan_info` while networks map to VLAN 1 (`_client_access.py:84-91` vs
  `vlans.py:10-12`); `_normalize_wan_speed` turns a genuine 100 Mbps WAN into
  100 Gbps (add bounds sanity) (`wan.py:9-19`); bare `"ap" in name` classify
  substring false-positives ("Apollo") (`_classify_device.py:12-21, 48-49`);
  `extract_port_number`/eth0 0-based off-by-one (`ports.py:8-15`).
- [ ] **F54 Model minor structure group** - `topology.py:50-95` duplicates
  `clients.client_matches_filters`; `collapse_client_edges` mutates its
  arguments and returns values (`clients.py:217-237`); `_collect_lldp_links`
  takes 8 params that are `EdgeDiscoveryResult` fields
  (`_edge_discovery.py:199-224`); dead only_unifi guard in
  `_resolve_uplink_target` (`:227-240`); untyped 5-tuple
  `_device_display_fields` (`_topology_device_coerce.py:82-92`) and 4-tuple
  `_client_inventory_identity` (`inventory.py:118-126`); `Device` frozen
  dataclass with unhashable list fields generates a hash that raises
  (`_topology_types.py:46-64`); LAG/parallel edges silently collapse - add
  comment (`_edge_discovery.py:156-179`, `diff.py:396-398`);
  `_primary_vlan_for_node` docstring contradicts behavior (`edges.py:280-290`);
  `wan.py:149` mypy-style ignore instead of narrowing; inventory
  Iterable/Sequence/list parameter inconsistency.
- [ ] **F55 Mock/dependency hygiene** - star-import of `unifi_topology.model`
  raises raw `ModuleNotFoundError: faker` on prod installs (`MockOptions` in
  `__all__` triggers the lazy load); add a friendly ImportError in `mock.py`
  and consider a public `mock` extra; hoist duplicated `[1, 10, 20, 30, 100]`
  VLAN list to a constant (`mock.py:146, 331, 338`); split the two >15-line
  client builders; add basic mock tests (currently zero, excluded from
  coverage).
- [ ] **F56 SVG render minor group** - theme YAML cannot set vpn_*/group_*
  fields (never read in `theme.py:101-134`); `max_vlan_colors` dead parameter
  chain; `font_family` slug allows path traversal into the woff2 loader and
  unescaped CSS interpolation (restrict to `[a-z0-9-]`)
  (`svg_theme.py:253-263`); `capitalize()` mangles "IoT" to "Iot"
  (`svg_wan.py:50`, `_svg_iso_group_boundaries.py:117`); unused `gx` binding;
  `_groups_from_vlan_node_map` and alias exports have no callers; iso
  god-parameter lists (`_render_iso_poe_icon` 13 params,
  `_render_iso_node_icon` 16) - introduce an IsoFaceStyle/pass coords intact;
  long overlay renderers split into metrics/connector/box/labels like the
  ortho WAN path; unannotated sort_key params; document/name the iso magic
  constants.
- [ ] **F57 Text render minor group** - Jinja autoescape extensions never
  match `*.md.j2`/`*.html.j2` (autoescape effectively off)
  (`_templating.py:7-14`); headings interpolate `device_name`/`title`
  unescaped; mermaid legend template has duplicate/dead linkStyle+classDef
  lines and an undocumented `arrowhead:` property; `_lldp_sort_key`
  concatenates digits (`eth1/0/2` sorts as 102); `build_device_index` computed
  twice per lldp render; dead `theme` param in `_build_line_row`; dead
  `model=""` param in a test helper; respelled `ClientPortMap` alias.

## Verified non-issues (for the record)

- Faker does not leak into `import unifi_topology` (lazy `__getattr__` works).
- Atomic cache write (tmp + `replace` under lock) is sound.
- Stale-cache fallback respects `use_cache=False`.
- Edge dedup within one discovery pass is sound given consistent node IDs.
- `py.typed` is shipped; PEP 695 generics valid on the 3.12 floor.
- No `print` calls in library modules; complexity gates genuinely pass.
