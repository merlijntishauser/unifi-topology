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

## Built-in Themes

`unifi`, `unifi-dark`, `minimal`, `minimal-dark`, `classic`, `classic-dark`

## Related Projects

- **CLI tool**: [unifi-network-maps](https://github.com/merlijntishauser/unifi-network-maps)
- **Home Assistant integration**: [unifi-network-maps-ha](https://github.com/merlijntishauser/unifi-network-maps-ha)
