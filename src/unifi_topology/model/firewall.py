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
    # Source-side filtering
    source_ip_ranges: tuple[str, ...] = ()
    source_mac_addresses: tuple[str, ...] = ()
    source_port_ranges: tuple[str, ...] = ()
    source_network_id: str = ""
    # Destination-side filtering
    destination_mac_addresses: tuple[str, ...] = ()
    destination_network_id: str = ""
    # Firewall group references (IDs)
    source_port_group_id: str = ""
    destination_port_group_id: str = ""
    source_address_group_id: str = ""
    destination_address_group_id: str = ""
    # What each side matches on: "ANY", "IP", "CLIENT", "APP", "WEB", ...
    # A target other than "ANY" means the rule is narrowed, even when the
    # criteria are not parsed into one of the lists below. Empty means the
    # payload carried no target (older controllers).
    source_matching_target: str = ""
    destination_matching_target: str = ""
    # Destination matching beyond IP/MAC/network
    destination_web_domains: tuple[str, ...] = ()
    destination_web_matching_type: str = ""  # e.g. "CUSTOM" for an explicit list
    destination_app_ids: tuple[str, ...] = ()
    # Connection state / metadata
    connection_state_type: str = ""
    connection_logging: bool = False
    schedule: str = ""
    match_ip_sec: str = ""


@dataclass(frozen=True)
class FirewallGroup:
    """A firewall address or port group."""

    id: str
    name: str
    group_type: str  # "address-group", "port-group", "ipv6-address-group"
    members: tuple[str, ...] = ()
