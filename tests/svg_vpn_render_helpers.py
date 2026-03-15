"""Shared helpers for SVG VPN rendering tests."""

from __future__ import annotations

from unifi_topology.model.topology import Edge, VpnTunnel


def gateway_edges() -> list[Edge]:
    """Create the default gateway-to-switch edge list."""
    return [Edge("Gateway", "Switch")]


def gateway_node_types() -> dict[str, str]:
    """Create the default gateway node type map."""
    return {"Gateway": "gateway", "Switch": "switch"}


def vpn_tunnel(
    *,
    name: str = "Remote Site",
    remote_subnets: tuple[str, ...] = ("10.0.0.0/24",),
    ifname: str | None = "wgsts1000",
    up: bool = True,
    gateway_mac: str | None = None,
) -> VpnTunnel:
    """Create a VPN tunnel for render tests."""
    return VpnTunnel(
        name=name,
        vpn_type="sdwan-mesh-tunnel",
        remote_subnets=remote_subnets,
        ifname=ifname,
        enabled=True,
        up=up,
        gateway_mac=gateway_mac,
    )
