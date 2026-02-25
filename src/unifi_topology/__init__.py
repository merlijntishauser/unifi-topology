"""UniFi network topology discovery and SVG rendering library."""

__version__ = "0.1.0"

from .adapters import Config, fetch_clients, fetch_devices, fetch_networks, resolve_hostnames
from .model import (
    Device,
    DeviceInfo,
    Edge,
    TopologyResult,
    WanInfo,
    build_device_inventory,
    build_topology,
    extract_wan_info,
    normalize_devices,
)
from .render import (
    SvgOptions,
    SvgTheme,
    render_dual,
    render_svg,
    render_svg_isometric,
    resolve_svg_themes,
)

__all__ = [
    "Config",
    "Device",
    "DeviceInfo",
    "Edge",
    "SvgOptions",
    "SvgTheme",
    "TopologyResult",
    "WanInfo",
    "build_device_inventory",
    "build_topology",
    "extract_wan_info",
    "fetch_clients",
    "fetch_devices",
    "fetch_networks",
    "normalize_devices",
    "render_dual",
    "render_svg",
    "render_svg_isometric",
    "resolve_hostnames",
    "resolve_svg_themes",
]
