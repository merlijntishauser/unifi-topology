# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] (2026-03-17)

### Added
- Generic Mermaid diagram rendering (`render_mermaid`, `MermaidTheme`)
- Markdown device port overview tables (`render_device_port_overview`)
- LLDP Markdown table rendering (`render_lldp_md`)
- Jinja2 template engine for render output
- Enables downstream consumers (unifi-homelab-ops) to use renderers directly

### Fixed
- Model lookup for 3 devices returning empty names by adding scraper aliases for controller model codes (`UDMA6A8`/`UCGF`, `UAPA693`/`G7LT`, `USWED37`/`USM25G8P`) (fixes #23)

## [1.2.4] (2026-03-16)

### Added
- Model lookup now resolves firmware platform codes (e.g. `U6M`, `UDMPRO`) in addition to store SKUs (fixes #23)
- `lookup_model_docs()` and `lookup_firmware_changelog()` for documentation and release notes links
- Scraper extended to cross-reference the official Ubiquiti firmware API with the store, including datasheet and firmware changelog URLs

## [1.2.3] (2026-03-16)

### Fixed
- Incomplete URL substring sanitization in test suite (CodeQL #193)
- `models.json` not included in PyPI wheel, causing model name lookup to silently return empty (fixes #22)

## [1.2.2] (2026-03-15)

### Added
- Model name lookup table scraped from the official Ubiquiti store (`lookup_model_name`, `lookup_model_url`)
- `normalize_device_stats` now resolves `model_name` from the lookup table when the API omits it (fixes #21)
- `make scrape-models` target and `scripts/scrape_models.py` scraper for refreshing the bundled model data

## [1.2.1] (2026-03-15)

### Added
- `model_name` field on `DeviceStats` for friendly device names (fixes #19)
- Release notes and API notes documenting `1.2.1` compatibility expectations and release verification

### Changed
- Tightened source complexity enforcement to `A/A/A` and completed the internal adapter, model, and render refactor behind stable public exports
- Reorganized the test suite into focused modules and reduced every `tests/test_*.py` file to `100` lines or fewer for lower navigation cost
- Expanded API contract coverage so README-style usage and top-level exports/signatures are validated in CI

### Fixed
- Cache serializer now preserves `state`, `uptime`, `num_sta`, `system-stats`, temperature, traffic counters, and PoE budget fields (fixes #20)
- Corrected README and documentation examples to match the current stable library contract and rendering workflow

## [1.2.0] (2026-03-15)

### Added
- `fetch_device_stats()` for device CPU, memory, temperature, and PoE metrics
- `DeviceStats` and `PoePortStats` data models with `normalize_device_stats()` coercion

### Changed
- Test coverage boosted to 98% across all modules (899 tests)
- Consolidated fetch functions to use shared `_fetch_cached` helper, improving maintainability index to A

## [1.1.1] (2026-03-14)

### Added
- Cache invalidation: `invalidate_cache` for clearing cached API responses after write operations
- `UnifiClient` instance caching per config to avoid repeated logins and prevent 429 rate-limit errors
- `clear_client_cache()` for explicit client cache control
- `UnifiError` base exception class so consumers can catch all unifi-topology errors with a single `except UnifiError`
- Export `UnifiApiError` and `UnifiAuthError` from the public API


## [1.1.0] (2026-03-12)

### Added
- Firewall policy write operations: `toggle_firewall_policy` and `swap_firewall_policy_order`
- `pip-audit` dependency vulnerability scanning in CI and Makefile

### Changed
- CI quality checks (lint, typecheck, complexity, audit) now run in parallel instead of sequentially

## [1.0.8] (2026-03-12)

### Added
- Extended `FirewallPolicy` with source-side filtering fields: `source_ip_ranges`, `source_mac_addresses`, `source_port_ranges`, `source_network_id`
- Added destination-side fields: `destination_mac_addresses`, `destination_network_id`
- Added firewall group references: `source_port_group_id`, `destination_port_group_id`, `source_address_group_id`, `destination_address_group_id`
- Added connection/metadata fields: `connection_state_type`, `connection_logging`, `schedule`, `match_ip_sec`
- Normalization extracts all new fields from both flat and nested (v2 API) formats

## [1.0.5] (2026-03-09)

### Added
- Firewall support: `FirewallZone`, `FirewallPolicy`, `FirewallGroup` data models with normalization and flexible field name resolution
- `fetch_firewall_zones`, `fetch_firewall_policies`, `fetch_firewall_groups` with cache/retry/stale-cache fallback
- V2/Integration API support in `UnifiClient` (`_get_v2` method) for zone and policy endpoints

### Changed
- Relaxed runtime dependency pins from exact versions to compatible ranges to reduce conflicts with downstream consumers

## [1.0.4] (2026-02-28)

### Fixed
- `network_table` field lost during device cache serialization, breaking VPN tunnel extraction from cached data

## [1.0.3] (2026-02-28)

### Added
- VPN tunnel support: extraction from gateway device data and SVG rendering
- MkDocs documentation site with API reference, deployed to GitHub Pages
- `make docs` / `make docs-serve` / `make version-bump` targets
- `CONTRIBUTING.md`, issue templates, PR template
- `py.typed` marker for PEP 561 type checking support
- README badges (CI, PyPI, Python version, license)

### Changed
- Expanded `SECURITY.md` with supported versions, response timeline, and scope

## [1.0.1] (2026-02-25)

First stable release, extracted from `unifi-network-maps` v1.6.x.

### Added
- `adapters` -- UniFi API client, environment config, DNS hostname resolution
- `model` -- Topology model, device normalization, edge building, client handling, VLAN info, diff/snapshot, mock data generation
- `render` -- SVG orthogonal and isometric rendering, theming, icons, inventory tables
- `paths` -- Path validation helpers for secure file access
- Assets: SVG device icons (isometric, modern, modern-flat), theme YAML files, embedded fonts
- Full public API exported from top-level package: `build_client_edges`, `build_device_index`, `build_node_type_map`, `group_devices_by_type`, `DEFAULT_SVG_THEME`
- PyPI trusted publishing via GitHub Actions
- Dependabot and CodeQL workflows

[Unreleased]: https://github.com/merlijntishauser/unifi-topology/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/merlijntishauser/unifi-topology/compare/v1.2.4...v1.3.0
[1.2.4]: https://github.com/merlijntishauser/unifi-topology/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/merlijntishauser/unifi-topology/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/merlijntishauser/unifi-topology/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/merlijntishauser/unifi-topology/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/merlijntishauser/unifi-topology/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/merlijntishauser/unifi-topology/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.8...v1.1.0
[1.0.8]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.5...v1.0.8
[1.0.5]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/merlijntishauser/unifi-topology/releases/tag/v1.0.1
