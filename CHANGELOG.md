# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.5...HEAD
[1.0.5]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/merlijntishauser/unifi-topology/releases/tag/v1.0.1