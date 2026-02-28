"""UniFi network topology discovery and SVG rendering library."""

__version__ = "1.0.2"

from .adapters import Config, fetch_clients, fetch_devices, fetch_networks, resolve_hostnames
from .model import (
    Device,
    DeviceInfo,
    Edge,
    TopologyResult,
    VpnTunnel,
    WanInfo,
    build_client_edges,
    build_device_index,
    build_device_inventory,
    build_node_type_map,
    build_topology,
    extract_vpn_tunnels,
    extract_wan_info,
    group_devices_by_type,
    normalize_devices,
)
from .render import (
    DEFAULT_SVG_THEME,
    SvgOptions,
    SvgTheme,
    render_dual,
    render_svg,
    render_svg_isometric,
    resolve_svg_themes,
)

__all__ = [
    "Config",
    "DEFAULT_SVG_THEME",
    "Device",
    "DeviceInfo",
    "Edge",
    "SvgOptions",
    "SvgTheme",
    "TopologyResult",
    "VpnTunnel",
    "WanInfo",
    "build_client_edges",
    "build_device_index",
    "build_device_inventory",
    "build_node_type_map",
    "build_topology",
    "extract_vpn_tunnels",
    "extract_wan_info",
    "fetch_clients",
    "fetch_devices",
    "fetch_networks",
    "group_devices_by_type",
    "normalize_devices",
    "render_dual",
    "render_svg",
    "render_svg_isometric",
    "resolve_hostnames",
    "resolve_svg_themes",
]
