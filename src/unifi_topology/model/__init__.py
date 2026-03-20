"""Network topology model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .clients import build_client_edges, build_node_type_map
from .device_stats import DeviceStats, PoePortStats
from .device_stats_coerce import normalize_device_stats
from .edges import build_device_index, build_topology, group_devices_by_type, group_nodes_by_vlan
from .firewall import FirewallGroup, FirewallPolicy, FirewallZone
from .firewall_coerce import (
    normalize_firewall_groups,
    normalize_firewall_policies,
    normalize_firewall_zones,
)
from .inventory import DeviceInfo, build_device_inventory
from .model_lookup import (
    list_all_models,
    lookup_firmware_changelog,
    lookup_model_docs,
    lookup_model_name,
    lookup_model_specs,
    lookup_model_url,
)
from .topology import Device, Edge, TopologyResult, VpnTunnel, WanInfo
from .topology_coerce import normalize_devices
from .vpn import extract_vpn_tunnels
from .wan import extract_wan_info

if TYPE_CHECKING:
    from .mock import MockOptions, generate_mock_payload

__all__ = [
    "Device",
    "DeviceInfo",
    "DeviceStats",
    "Edge",
    "FirewallGroup",
    "FirewallPolicy",
    "FirewallZone",
    "MockOptions",
    "PoePortStats",
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
    "generate_mock_payload",
    "group_devices_by_type",
    "group_nodes_by_vlan",
    "list_all_models",
    "lookup_firmware_changelog",
    "lookup_model_docs",
    "lookup_model_name",
    "lookup_model_specs",
    "lookup_model_url",
    "normalize_device_stats",
    "normalize_devices",
    "normalize_firewall_groups",
    "normalize_firewall_policies",
    "normalize_firewall_zones",
]


def __getattr__(name: str) -> object:
    if name in ("MockOptions", "generate_mock_payload"):
        from .mock import MockOptions, generate_mock_payload

        globals()["MockOptions"] = MockOptions
        globals()["generate_mock_payload"] = generate_mock_payload
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
