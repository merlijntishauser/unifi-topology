# CLAUDE.md

Quick reference for AI assistants working on this codebase.

## Project Overview

**unifi-topology** - A Python library for UniFi network topology discovery and diagram rendering (SVG orthogonal/isometric, Mermaid, and Markdown/LLDP tables). Extracted from `unifi-network-maps` to provide a clean API for programmatic use.

- **Version**: 2.2.2
- **Python**: 3.12+ (3.13 preferred)
- **License**: MIT
- **PyPI**: `pip install unifi-topology`

## Architecture

```
Source (UniFi API) -> Model (devices/topology) -> Render (SVG/Mermaid/Markdown) -> Output (string)
```

### Source Layout

Modules prefixed with `_` are private implementation helpers; the public API is
re-exported from `unifi_topology/__init__.py`. Only the load-bearing modules are
listed below.

```
src/unifi_topology/
├── __init__.py          # Public API re-exports
├── paths.py             # Path validation helpers
├── adapters/
│   ├── config.py        # Environment/config loading (Config)
│   ├── dns.py           # Reverse DNS hostname resolution
│   ├── unifi.py         # UniFi API adapter (caching, retries, auth fallback)
│   ├── unifi_api.py     # Thin HTTP client for UniFi controller (UnifiError hierarchy)
│   ├── _cache_store.py  # Cache storage, locking, safety checks
│   ├── _cache_serialize.py # Device/network cache serialization
│   ├── _fetch.py        # Fetch-with-cache orchestration
│   └── _retry.py        # Retry policy and request timeout
├── model/
│   ├── topology.py      # Core topology model (Topology, Device, Edge, snapshot version)
│   ├── topology_coerce.py / _topology_device_coerce.py / _topology_port_coerce.py  # API data normalization
│   ├── clients.py, classify.py, connection.py  # Client handling and classification
│   ├── edges.py, _edge_discovery.py  # Edge building, port maps, grouping
│   ├── firewall.py, firewall_coerce.py  # Firewall zones/policies model
│   ├── device_stats.py, device_stats_coerce.py  # Device statistics
│   ├── vpn.py           # VPN tunnel extraction
│   ├── wan.py           # WAN upstream info extraction
│   ├── vlans.py, ports.py, lldp.py, labels.py, inventory.py, helpers.py
│   ├── mock.py          # Mock data generation (lazy-loaded; requires dev Faker)
│   ├── snapshot.py      # Topology serialization
│   └── diff.py          # Topology change detection
├── render/
│   ├── svg.py, svg_isometric.py  # SVG orthogonal / isometric output
│   ├── svg_theme.py, svg_layout.py, svg_edges.py, svg_labels.py, svg_icons.py
│   ├── svg_wan.py, svg_vpn.py  # SVG WAN / VPN overlays
│   ├── theme.py         # Theme loading (SVG)
│   ├── mermaid.py, mermaid_theme.py  # Mermaid diagram output
│   ├── markdown.py, lldp.py  # Markdown device/LLDP tables (uses Jinja2 templates)
│   ├── inventory.py     # Inventory table rendering
│   ├── templates/       # Jinja2 templates (*.j2)
│   └── _svg_*, _markdown_*  # Private rendering helpers
└── assets/
    ├── icons/           # SVG device icons (isometric, modern, modern-flat, icons-unifi)
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
- Max cyclomatic complexity per function: 5 (enforced by CI via ruff mccabe, xenon, and scripts/check_complexity.sh)
- Typing (pyright standard mode)
- No prints in library modules (use `logging`)
- Pure functions where possible
- This is a library: no CLI concerns, no file I/O beyond caching. Markdown/LLDP rendering uses Jinja2 templates under `render/templates/`.

## Key Dependencies

- `requests` - HTTP client
- `python-dotenv` - Environment loading
- `PyYAML` - Theme configuration
- `Jinja2` - Markdown/LLDP table templates
- `dnspython` - Reverse DNS hostname resolution
- `Faker` (dev) - Mock data generation

## Related Projects

- CLI tool: https://github.com/merlijntishauser/unifi-network-maps
- Home Assistant integration: https://github.com/merlijntishauser/unifi-network-maps-ha
