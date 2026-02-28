"""Tests for VPN tunnel extraction."""

from __future__ import annotations

from unifi_topology.model.topology import Device
from unifi_topology.model.vpn import extract_vpn_tunnels


def _gateway_device(
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


def _switch_device() -> Device:
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


def _vpn_entry(
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


class TestExtractVpnTunnels:
    def test_extract_from_gateway(self):
        device = _gateway_device(network_table=[_vpn_entry()])
        tunnels = extract_vpn_tunnels(device)
        assert len(tunnels) == 1
        tunnel = tunnels[0]
        assert tunnel.name == "Remote Site"
        assert tunnel.vpn_type == "sdwan-mesh-tunnel"
        assert tunnel.remote_subnets == ("10.0.0.0/24",)
        assert tunnel.ifname == "wgsts1000"
        assert tunnel.enabled is True
        assert tunnel.up is True
        assert tunnel.gateway_mac == "aa:bb:cc:dd:ee:01"

    def test_extract_non_gateway(self):
        device = _switch_device()
        tunnels = extract_vpn_tunnels(device)
        assert tunnels == []

    def test_extract_no_network_table(self):
        device = _gateway_device(network_table=[])
        tunnels = extract_vpn_tunnels(device)
        assert tunnels == []

    def test_tunnel_up_status(self):
        device = _gateway_device(network_table=[_vpn_entry(up="true")])
        tunnels = extract_vpn_tunnels(device)
        assert tunnels[0].up is True

    def test_tunnel_down_status(self):
        device = _gateway_device(network_table=[_vpn_entry(up="false")])
        tunnels = extract_vpn_tunnels(device)
        assert tunnels[0].up is False

    def test_multiple_tunnels(self):
        entries = [
            _vpn_entry(name="Site A", up="true"),
            _vpn_entry(name="Site B", up="false"),
        ]
        device = _gateway_device(network_table=entries)
        tunnels = extract_vpn_tunnels(device)
        assert len(tunnels) == 2
        assert tunnels[0].name == "Site A"
        assert tunnels[0].up is True
        assert tunnels[1].name == "Site B"
        assert tunnels[1].up is False

    def test_ignores_non_vpn_entries(self):
        entries = [
            {"purpose": "corporate", "name": "LAN"},
            _vpn_entry(name="VPN Tunnel"),
            {"purpose": "wan", "name": "WAN"},
        ]
        device = _gateway_device(network_table=entries)
        tunnels = extract_vpn_tunnels(device)
        assert len(tunnels) == 1
        assert tunnels[0].name == "VPN Tunnel"

    def test_disabled_tunnel(self):
        device = _gateway_device(network_table=[_vpn_entry(enabled=False)])
        tunnels = extract_vpn_tunnels(device)
        assert tunnels[0].enabled is False

    def test_multiple_remote_subnets(self):
        subnets = ["10.0.0.0/24", "172.16.0.0/16"]
        device = _gateway_device(network_table=[_vpn_entry(remote_subnets=subnets)])
        tunnels = extract_vpn_tunnels(device)
        assert tunnels[0].remote_subnets == ("10.0.0.0/24", "172.16.0.0/16")

    def test_missing_optional_fields(self):
        entry = {"purpose": "site-vpn", "name": "Minimal"}
        device = _gateway_device(network_table=[entry])
        tunnels = extract_vpn_tunnels(device)
        assert len(tunnels) == 1
        assert tunnels[0].name == "Minimal"
        assert tunnels[0].ifname is None
        assert tunnels[0].remote_subnets == ()
