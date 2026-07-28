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

- `Config` -- Configuration from environment variables (`UNIFI_URL`, `UNIFI_USER`/`UNIFI_PASS` or `UNIFI_API_KEY`, etc.)
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

Built-in themes: `unifi`, `unifi-dark`, `minimal`, `minimal-dark`, `classic`,
`classic-dark`, `blueprint` (white line work on blueprint-blue paper --
monochrome outlines, white icons, graph-paper grid)

### Isometric render options

`render_svg_isometric` has several refinements. The four listed first **default
to off**, so upgrading never changes an existing diagram -- turn on the ones you
want.

```python
from unifi_topology.render.svg_theme import SvgOptions, SvgTheme, DEFAULT_THEME
import dataclasses

options = SvgOptions(
    iso_compact_layout=True,  # group devices instead of one long diagonal
    iso_route_around_nodes=True,  # route links around intervening devices
    iso_lighting=True,  # shaded side faces and contact shadows
    iso_show_grid=False,  # hide the isometric floor grid (on by default)
)
theme = dataclasses.replace(DEFAULT_THEME, icon_set="unifi")

svg = render_svg_isometric(edges, node_types=types, options=options, theme=theme)
```

| Option | Where | What it changes |
| --- | --- | --- |
| `iso_compact_layout` | `SvgOptions` | Packs each device and its clients into a block, and each block beneath its parent. The default maps sibling order to one grid axis and tree depth to the other; because home networks are shallow and wide, that draws everything along a single diagonal. On a 50-node network this takes the canvas from 11904x6892 to 5424x4397. Also guarantees one node per grid cell -- the default can place two devices on the same tile. |
| `iso_route_around_nodes` | `SvgOptions` | Picks the link corner that crosses fewest devices, and steps into a clear lane when every simple route is blocked. Without it the corner is always taken on the same axis, so links are drawn over unrelated devices and their labels (20 of 31 links on that same network; 0 with it on). Legs stay grid-aligned either way, so they always project to true isometric lines. |
| `iso_lighting` | `SvgOptions` | Shades each tile's side faces from its own colour under one light direction, and seats it with a contact shadow. |
| `icon_set` | `SvgTheme` | `isometric` (default, isopacks artwork), `modern`, or `unifi`. |
| `iso_show_grid` | `SvgOptions` | Draws the isometric floor grid behind the diagram. **On by default** -- set `False` for a plain background. Nothing else about the render changes, including the canvas size. |

#### Icon sets

| Set | Contents |
| --- | --- |
| `isometric` | Default. [isopacks](https://github.com/markmanx/isopacks) artwork (MIT). Generic rather than network-specific: access points are radio masts, NAS is a database cylinder, a client cluster is a person. Four subjects isopacks does not cover -- camera, speaker, games console, sensor -- are supplied from the `unifi` set, restyled into the isopacks palette. |
| `modern` | Flat icons with a per-type accent colour. |
| `unifi` | Original MIT artwork drawn for this project, one file per node type with no fallbacks. Devices look like the hardware they represent. Neutral grey-white bodies with a cyan accent -- a different visual family from `isometric`, so pick one rather than mixing. |

Rendered comparisons of each option live in [`docs/examples/`](docs/examples/).

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
