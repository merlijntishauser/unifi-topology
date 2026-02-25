# unifi-topology

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
    fetch_devices,
    fetch_networks,
    normalize_devices,
    build_topology,
    extract_wan_info,
    render_svg,
    resolve_svg_themes,
    SvgOptions,
)

# Connect to UniFi controller
config = Config.from_env()
raw_devices = fetch_devices(config)
networks = fetch_networks(config)

# Build topology model
devices = normalize_devices(raw_devices)
result = build_topology(devices, include_ports=True, only_unifi=False)
wan_info = extract_wan_info(devices, list(networks))

# Render SVG
theme = resolve_svg_themes(theme_name="unifi")
options = SvgOptions(include_ports=True)
svg = render_svg(result.devices, result.edges, theme=theme, options=options, wan_info=wan_info)
```

## API Overview

### Adapters

- `Config` -- Configuration from environment variables (`UNIFI_URL`, `UNIFI_USER`, `UNIFI_PASS`, etc.)
- `fetch_devices(config)` -- Fetch device list from UniFi controller
- `fetch_clients(config)` -- Fetch active clients
- `fetch_networks(config)` -- Fetch network/VLAN configuration
- `resolve_hostnames(ips, dns_server)` -- Reverse DNS resolution

### Model

- `normalize_devices(raw)` -- Convert raw API data to `Device` objects
- `build_topology(devices, ...)` -- Build topology graph (`TopologyResult` with devices + edges)
- `build_device_inventory(devices)` -- Build device info table (`list[DeviceInfo]`)
- `extract_wan_info(devices, networks)` -- Extract WAN upstream info

### Rendering

- `render_svg(devices, edges, theme, options, ...)` -- Orthogonal SVG diagram
- `render_svg_isometric(devices, edges, theme, options, ...)` -- Isometric 3D-style SVG
- `render_dual(devices, edges, themes, options, ...)` -- Dual light/dark theme SVG
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

## License

MIT
