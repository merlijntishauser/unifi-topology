"""Firewall zone and policy data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FirewallZone:
    """A firewall security zone."""

    id: str
    name: str
    network_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FirewallPolicy:
    """A zone-based firewall policy rule."""

    id: str
    name: str
    enabled: bool
    action: str  # "ALLOW", "BLOCK", "REJECT", "DROP"
    source_zone_id: str
    destination_zone_id: str
    protocol: str = "all"
    port_ranges: tuple[str, ...] = ()
    ip_ranges: tuple[str, ...] = ()
    description: str = ""
    index: int = 0
    predefined: bool = False


@dataclass(frozen=True)
class FirewallGroup:
    """A firewall address or port group."""

    id: str
    name: str
    group_type: str  # "address-group", "port-group", "ipv6-address-group"
    members: tuple[str, ...] = ()
