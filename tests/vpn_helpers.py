"""Shared VPN test helpers."""

from __future__ import annotations

from unifi_topology.model.topology import Device


def gateway_device(
    network_table: list[dict] | None = None,
    mac: str = "aa:bb:cc:dd:ee:01",
) -> Device:
    """Create a minimal gateway device for testing."""
    return Device(
        name="Gateway",
        model_name="UDM Pro",
        model="UDM-Pro",
        mac=mac,
        ip="192.168.1.1",
        type="ugw",
        lldp_info=[],
        network_table=network_table or [],
    )


def switch_device() -> Device:
    """Create a minimal switch device for testing."""
    return Device(
        name="Switch",
        model_name="USW-24",
        model="USW-24",
        mac="aa:bb:cc:dd:ee:02",
        ip="192.168.1.2",
        type="usw",
        lldp_info=[],
    )


def vpn_entry(
    *,
    name: str = "Remote Site",
    vpn_type: str = "sdwan-mesh-tunnel",
    up: str = "true",
    enabled: bool = True,
    ifname: str = "wgsts1000",
    remote_subnets: list[str] | None = None,
) -> dict:
    """Create a site-vpn network_table entry."""
    return {
        "purpose": "site-vpn",
        "name": name,
        "vpn_type": vpn_type,
        "up": up,
        "enabled": enabled,
        "ifname": ifname,
        "remote_vpn_subnets": remote_subnets or ["10.0.0.0/24"],
    }
