"""Tests for basic VPN tunnel extraction behavior."""

from __future__ import annotations

from tests.vpn_helpers import gateway_device, switch_device, vpn_entry
from unifi_topology.model.vpn import extract_vpn_tunnels


class TestExtractVpnTunnelsBasic:
    def test_extract_from_gateway(self):
        device = gateway_device(network_table=[vpn_entry()])
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
        assert extract_vpn_tunnels(switch_device()) == []

    def test_extract_no_network_table(self):
        assert extract_vpn_tunnels(gateway_device(network_table=[])) == []

    def test_ignores_non_vpn_entries(self):
        entries = [
            {"purpose": "corporate", "name": "LAN"},
            vpn_entry(name="VPN Tunnel"),
            {"purpose": "wan", "name": "WAN"},
        ]

        tunnels = extract_vpn_tunnels(gateway_device(network_table=entries))

        assert len(tunnels) == 1
        assert tunnels[0].name == "VPN Tunnel"

    def test_multiple_tunnels(self):
        entries = [
            vpn_entry(name="Site A", up="true"),
            vpn_entry(name="Site B", up="false"),
        ]

        tunnels = extract_vpn_tunnels(gateway_device(network_table=entries))

        assert len(tunnels) == 2
        assert tunnels[0].name == "Site A"
        assert tunnels[0].up is True
        assert tunnels[1].name == "Site B"
        assert tunnels[1].up is False
