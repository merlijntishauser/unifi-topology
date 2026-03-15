"""Tests for VPN tunnel state and field extraction."""

from __future__ import annotations

from tests.vpn_helpers import gateway_device, vpn_entry
from unifi_topology.model.vpn import extract_vpn_tunnels


class TestExtractVpnTunnelStates:
    def test_tunnel_up_status(self):
        tunnels = extract_vpn_tunnels(gateway_device(network_table=[vpn_entry(up="true")]))
        assert tunnels[0].up is True

    def test_tunnel_down_status(self):
        tunnels = extract_vpn_tunnels(gateway_device(network_table=[vpn_entry(up="false")]))
        assert tunnels[0].up is False

    def test_disabled_tunnel(self):
        tunnels = extract_vpn_tunnels(gateway_device(network_table=[vpn_entry(enabled=False)]))
        assert tunnels[0].enabled is False

    def test_multiple_remote_subnets(self):
        subnets = ["10.0.0.0/24", "172.16.0.0/16"]
        tunnels = extract_vpn_tunnels(
            gateway_device(network_table=[vpn_entry(remote_subnets=subnets)])
        )
        assert tunnels[0].remote_subnets == ("10.0.0.0/24", "172.16.0.0/16")

    def test_missing_optional_fields(self):
        entry = {"purpose": "site-vpn", "name": "Minimal"}
        tunnels = extract_vpn_tunnels(gateway_device(network_table=[entry]))

        assert len(tunnels) == 1
        assert tunnels[0].name == "Minimal"
        assert tunnels[0].ifname is None
        assert tunnels[0].remote_subnets == ()
