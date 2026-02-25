# CLAUDE.md

Quick reference for AI assistants working on this codebase.

## Project Overview

**unifi-topology** - A Python library for UniFi network topology discovery and SVG diagram rendering. Extracted from `unifi-network-maps` to provide a clean API for programmatic use.

- **Version**: 0.1.0
- **Python**: 3.12+ (3.13 preferred)
- **License**: MIT
- **PyPI**: `pip install unifi-topology`

## Architecture

```
Source (UniFi API) -> Model (devices/topology) -> Render (SVG) -> Output (string)
```

### Source Layout

```
src/unifi_topology/
├── __init__.py          # Public API re-exports
├── paths.py             # Path validation helpers
├── adapters/
│   ├── config.py        # Environment/config loading
│   ├── dns.py           # Reverse DNS hostname resolution
│   ├── unifi.py         # UniFi API adapter (caching, retries)
│   └── unifi_api.py     # Thin HTTP client for UniFi controller
├── model/
│   ├── topology.py      # Core topology model (Device, Edge, etc.)
│   ├── topology_coerce.py # Raw API data normalization
│   ├── clients.py       # Client device handling and filtering
│   ├── classify.py      # Device/client type classification
│   ├── connection.py    # Wireless connection quality
│   ├── edges.py         # Edge building, port maps, grouping
│   ├── helpers.py       # Shared low-level helpers
│   ├── inventory.py     # Device inventory model (DeviceInfo)
│   ├── lldp.py          # LLDP parsing
│   ├── labels.py        # Label generation
│   ├── ports.py         # Port handling
│   ├── vlans.py         # VLAN inventory
│   ├── wan.py           # WAN upstream info extraction
│   ├── mock.py          # Mock data generation (uses Faker)
│   ├── snapshot.py      # Topology serialization
│   └── diff.py          # Topology change detection
├── render/
│   ├── svg.py           # SVG orthogonal output
│   ├── svg_isometric.py # SVG isometric output
│   ├── svg_theme.py     # SVG theming (SvgTheme, SvgOptions)
│   ├── svg_layout.py    # SVG layout algorithms
│   ├── svg_edges.py     # SVG edge rendering
│   ├── svg_labels.py    # SVG label rendering
│   ├── svg_icons.py     # SVG icon loading
│   ├── svg_wan.py       # SVG WAN upstream rendering
│   ├── svg_iso_geometry.py  # Isometric coordinate math
│   ├── svg_iso_nodes.py     # Isometric node rendering
│   ├── svg_iso_edges.py     # Isometric edge rendering
│   ├── inventory.py     # Inventory table rendering
│   └── theme.py         # Theme loading (SVG only)
└── assets/
    ├── icons/           # SVG device icons (isometric, modern, modern-flat)
    ├── themes/          # Default theme YAML files
    └── fonts/           # Embedded web fonts (woff2)
```

## Development Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Quality
ruff check .
ruff format .
pyright

# Testing
pytest                    # All tests
pytest -m unit            # Unit tests
pytest -m integration     # Integration tests
pytest -m contract        # Contract tests

# Coverage
pytest --cov=unifi_topology --cov-report=term-missing

# CI
make ci                   # Run all checks
```

## Testing

- **Unit tests**: `tests/` - pytest (auto-marked by conftest.py)
- **Contract tests**: `tests/test_contract_unifi.py` - fixture-based
- **Live contract tests**: Set `UNIFI_CONTRACT_LIVE=1` with UniFi env vars

## Code Quality Guidelines

- Clear, intention-revealing names
- Optimize for readability over cleverness
- Small, safe refactors; commit often
- Functions > 15 lines are a code smell
- Max cyclomatic complexity per function: 12 (enforced by CI)
- Typing (pyright standard mode)
- No prints in library modules (use `logging`)
- Pure functions where possible
- This is a library: no CLI concerns, no Jinja2 templates, no file I/O beyond caching

## Key Dependencies

- `requests` - HTTP client
- `python-dotenv` - Environment loading
- `PyYAML` - Theme configuration
- `dnspython` - Reverse DNS hostname resolution
- `Faker` (dev) - Mock data generation

## Related Projects

- CLI tool: https://github.com/merlijntishauser/unifi-network-maps
- Home Assistant integration: https://github.com/merlijntishauser/unifi-network-maps-ha
