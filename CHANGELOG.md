# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## 1.0.1 (2026-02-25)

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

[Unreleased]: https://github.com/merlijntishauser/unifi-topology/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/merlijntishauser/unifi-topology/releases/tag/v1.0.1