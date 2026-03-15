# unifi-topology

[![CI](https://github.com/merlijntishauser/unifi-topology/actions/workflows/ci.yml/badge.svg)](https://github.com/merlijntishauser/unifi-topology/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/unifi-topology)](https://pypi.org/project/unifi-topology/)
[![PyPI - Downloads](https://img.shields.io/pypi/dw/unifi-topology)](https://pypi.org/project/unifi-topology/)
[![Python](https://img.shields.io/pypi/pyversions/unifi-topology)](https://pypi.org/project/unifi-topology/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Python library for UniFi network topology discovery and SVG diagram rendering.

Extracted from [unifi-network-maps](https://github.com/merlijntishauser/unifi-network-maps) to provide a clean library API for programmatic use, including the [Home Assistant integration](https://github.com/merlijntishauser/unifi-network-maps-ha).

## Installation

```bash
pip install unifi-topology
```

## Quick Start

```python
from unifi_topology import (
    Config,
    SvgOptions,
    build_node_type_map,
    build_topology,
    extract_wan_info,
    fetch_devices,
    fetch_networks,
    normalize_devices,
    render_svg,
    resolve_svg_themes,
)

# Connect to UniFi controller
config = Config.from_env()
api_devices = fetch_devices(config)
networks = fetch_networks(config)

# Build topology model
devices = normalize_devices(api_devices)
node_types = build_node_type_map(devices)
gateways = [name for name, node_type in node_types.items() if node_type == "gateway"]
topology = build_topology(
    devices,
    include_ports=True,
    only_unifi=False,
    gateways=gateways,
)
gateway = next((device for device in devices if node_types.get(device.name) == "gateway"), None)
wan_info = extract_wan_info(gateway) if gateway else None

# Render SVG
theme = resolve_svg_themes(theme_name="unifi")
options = SvgOptions()
svg = render_svg(
    topology.tree_edges or topology.raw_edges,
    node_types=node_types,
    theme=theme,
    options=options,
    wan_info=wan_info,
)
```

## API Overview

### Adapters

- `Config` -- Configuration from environment variables (`UNIFI_URL`, `UNIFI_USER`, `UNIFI_PASS`, etc.)
- `fetch_devices(config)` -- Fetch device list from UniFi controller
- `fetch_clients(config)` -- Fetch active clients
- `fetch_networks(config)` -- Fetch network/VLAN configuration
- `fetch_firewall_zones(config)` -- Fetch firewall zone definitions
- `fetch_firewall_policies(config)` -- Fetch zone-based firewall policies
- `fetch_firewall_groups(config)` -- Fetch firewall address/port groups
- `resolve_hostnames(ips, dns_server)` -- Reverse DNS resolution

### Model

- `normalize_devices(raw)` -- Convert raw API data to `Device` objects
- `normalize_firewall_zones(raw)` -- Convert raw zone data to `FirewallZone` objects
- `normalize_firewall_policies(raw)` -- Convert raw policy data to `FirewallPolicy` objects
- `normalize_firewall_groups(raw)` -- Convert raw group data to `FirewallGroup` objects
- `build_node_type_map(devices, clients=None, ...)` -- Classify node names for rendering
- `build_topology(devices, *, include_ports, only_unifi, gateways)` -- Build topology graph (`TopologyResult` with `raw_edges` and `tree_edges`)
- `build_device_inventory(devices)` -- Build device info table (`list[DeviceInfo]`)
- `extract_wan_info(device, ...)` -- Extract WAN upstream info for a gateway device

### Rendering

- `render_svg(edges, *, node_types, theme, options, ...)` -- Orthogonal SVG diagram
- `render_svg_isometric(edges, *, node_types, theme, options, ...)` -- Isometric 3D-style SVG
- `render_dual(edges, *, node_types, theme, options, ...)` -- Physical + VLAN grouped SVG output
- `resolve_svg_themes(theme_name, theme_file)` -- Load built-in or custom SVG theme

Built-in themes: `unifi`, `unifi-dark`, `minimal`, `minimal-dark`, `classic`, `classic-dark`

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

make lint        # ruff check
make format      # ruff format
make typecheck   # pyright
make test        # pytest
make ci          # all checks
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT -- see [LICENSE](LICENSE). Third-party licenses in [LICENSES.md](LICENSES.md).
