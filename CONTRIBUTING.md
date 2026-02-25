# Contributing

Thanks for considering a contribution!

## Project Overview

**unifi-topology** is a Python library for UniFi network topology discovery and SVG diagram rendering, extracted from [unifi-network-maps](https://github.com/merlijntishauser/unifi-network-maps).

## Architecture

```
Source (UniFi API) -> Model (devices/topology) -> Render (SVG) -> Output (string)
```

### Module Structure

```
src/unifi_topology/
├── adapters/        # UniFi API client, config, DNS resolution
├── model/           # Topology model, edges, clients, VLANs, diff/snapshot
├── render/          # SVG orthogonal + isometric rendering, theming, icons
├── assets/          # SVG icons, theme YAML files, embedded fonts
└── paths.py         # Path validation helpers
```

### Key Concepts

- **Device**: Network device with type, name, MAC, model, ports
- **Edge**: Connection between devices with PoE status, VLAN, port info
- **TopologyResult**: Collection of raw and tree edges from topology discovery
- **SvgTheme**: Visual styling for SVG output

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Checks

```bash
make ci          # Run all checks (lint, format, typecheck, complexity, tests)
make lint        # ruff check
make format      # ruff format
make typecheck   # pyright
make test        # pytest
```

## Testing

| Type | Location | Command |
|------|----------|---------|
| Unit | `tests/` | `pytest -m unit` |
| Integration | `tests/` | `pytest -m integration` |
| Contract | `tests/test_contract_unifi.py` | `pytest -m contract` |
| Live contract | `tests/test_contract_unifi_live.py` | `UNIFI_CONTRACT_LIVE=1 pytest -m contract` |

Live contract tests require `UNIFI_CONTRACT_LIVE=1` plus UniFi environment variables (or a `.env` file).

## Code Guidelines

- Clear, intention-revealing names
- Small, focused functions (>15 lines is a code smell)
- Type annotations throughout (pyright standard mode)
- No prints in library modules (use `logging`)
- Pure functions where possible
- Add tests for behavior changes
- Run `make ci` before opening a PR

## This is a Library

This package is a library with no CLI. Keep it free of:
- CLI concerns (argument parsing, stdout printing)
- Jinja2 templates
- File I/O beyond caching

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `make ci` and ensure it passes
5. Open a pull request

## Release

Releases are published to PyPI automatically when a version tag is pushed:

```bash
git tag v1.x.x
git push origin v1.x.x
```

## Related Projects

- **CLI tool**: [unifi-network-maps](https://github.com/merlijntishauser/unifi-network-maps)
- **Home Assistant integration**: [unifi-network-maps-ha](https://github.com/merlijntishauser/unifi-network-maps-ha)

See `LICENSES.md` for third-party license info.
