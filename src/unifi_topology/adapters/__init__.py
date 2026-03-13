"""Adapters for external data sources."""

from .config import Config
from .dns import resolve_hostnames
from .unifi import (
    fetch_clients,
    fetch_devices,
    fetch_firewall_groups,
    fetch_firewall_policies,
    fetch_firewall_zones,
    fetch_networks,
    invalidate_cache,
    swap_firewall_policy_order,
    toggle_firewall_policy,
)
from .unifi_api import UnifiWriteError

__all__ = [
    "Config",
    "UnifiWriteError",
    "fetch_clients",
    "fetch_devices",
    "fetch_firewall_groups",
    "fetch_firewall_policies",
    "fetch_firewall_zones",
    "fetch_networks",
    "invalidate_cache",
    "resolve_hostnames",
    "swap_firewall_policy_order",
    "toggle_firewall_policy",
]
