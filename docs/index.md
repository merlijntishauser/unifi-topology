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

## Built-in Themes

`unifi`, `unifi-dark`, `minimal`, `minimal-dark`, `classic`, `classic-dark`

## Isometric Render Options

`render_svg_isometric` has four opt-in refinements, all off by default:

- `SvgOptions.iso_compact_layout` -- group devices into blocks instead of one long diagonal
- `SvgOptions.iso_route_around_nodes` -- route links around intervening devices
- `SvgOptions.iso_lighting` -- shaded side faces and contact shadows
- `SvgTheme.icon_set` -- `isometric` (default), `modern`, or `unifi`
- `SvgOptions.iso_show_grid` -- draw the isometric floor grid (on by default; set `False` to hide it)

See [Examples](examples/README.md) for rendered comparisons of each option on a
real network, and the
[README](https://github.com/merlijntishauser/unifi-topology#isometric-render-options)
for the full table of what each one changes.

## Release Notes

See the [release notes](release-notes.md) for compatibility notes, verification status, and upgrade guidance for the latest patch release.

## Related Projects

- **CLI tool**: [unifi-network-maps](https://github.com/merlijntishauser/unifi-network-maps)
- **Home Assistant integration**: [unifi-network-maps-ha](https://github.com/merlijntishauser/unifi-network-maps-ha)
