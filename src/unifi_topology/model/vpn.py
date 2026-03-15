"""VPN tunnel extraction from gateway devices."""

from __future__ import annotations

from typing import Any

from .classify import classify_device_type
from .topology import Device, VpnTunnel


def _site_vpn_entries(device: Device) -> list[dict[str, Any]]:
    return [entry for entry in device.network_table if entry.get("purpose") == "site-vpn"]


def _parse_remote_subnets(entry: dict[str, Any]) -> tuple[str, ...]:
    """Extract remote VPN subnets as a tuple of strings."""
    raw = entry.get("remote_vpn_subnets")
    if isinstance(raw, list):
        return tuple(str(s) for s in raw if isinstance(s, str))
    return ()


def _parse_bool_string(value: object) -> bool:
    """Parse a string boolean value (e.g., "true"/"false") to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def _vpn_tunnel(entry: dict[str, Any], *, gateway_mac: str) -> VpnTunnel:
    return VpnTunnel(
        name=str(entry.get("name", "")),
        vpn_type=str(entry.get("vpn_type", "")),
        remote_subnets=_parse_remote_subnets(entry),
        ifname=entry.get("ifname") if isinstance(entry.get("ifname"), str) else None,
        enabled=_parse_bool_string(entry.get("enabled", True)),
        up=_parse_bool_string(entry.get("up", False)),
        gateway_mac=gateway_mac,
    )


def extract_vpn_tunnels(device: Device) -> list[VpnTunnel]:
    """Extract VPN tunnel information from a gateway device.

    Reads the ``network_table`` entries with ``purpose == "site-vpn"``
    and returns a list of :class:`VpnTunnel` instances.

    Returns an empty list for non-gateway devices or when no VPN tunnels
    are configured.
    """
    if classify_device_type(device) != "gateway":
        return []
    if not device.network_table:
        return []
    return [_vpn_tunnel(entry, gateway_mac=device.mac) for entry in _site_vpn_entries(device)]
