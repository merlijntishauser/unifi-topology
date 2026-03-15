"""Tests for advanced SVG VPN rendering behavior."""

from __future__ import annotations

from unifi_topology.model.topology import Edge, VpnTunnel
from unifi_topology.render.svg import render_svg
from unifi_topology.render.svg_isometric import render_svg_isometric


class TestVpnRendering:
    def test_single_tunnel_up(self):
        tunnel = VpnTunnel(
            name="Remote Site",
            vpn_type="sdwan-mesh-tunnel",
            remote_subnets=("10.0.0.0/24",),
            ifname="wgsts1000",
            enabled=True,
            up=True,
            gateway_mac="aa:bb:cc:dd:ee:01",
        )
        output = render_svg(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            vpn_tunnels=[tunnel],
        )
        assert 'class="vpn-tunnels"' in output
        assert "Remote Site" in output
        assert "(UP)" in output

    def test_single_tunnel_down(self):
        tunnel = VpnTunnel(
            name="Remote Site",
            vpn_type="sdwan-mesh-tunnel",
            remote_subnets=(),
            ifname=None,
            enabled=True,
            up=False,
            gateway_mac=None,
        )
        output = render_svg(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            vpn_tunnels=[tunnel],
        )
        assert 'class="vpn-tunnels"' in output
        assert "(DOWN)" in output

    def test_multiple_tunnels(self):
        tunnels = [
            VpnTunnel(
                name="Site A",
                vpn_type="sdwan-mesh-tunnel",
                remote_subnets=("10.0.0.0/24",),
                ifname="wgsts1000",
                enabled=True,
                up=True,
                gateway_mac=None,
            ),
            VpnTunnel(
                name="Site B",
                vpn_type="sdwan-mesh-tunnel",
                remote_subnets=("172.16.0.0/16",),
                ifname="wgsts1001",
                enabled=True,
                up=False,
                gateway_mac=None,
            ),
        ]
        output = render_svg(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            vpn_tunnels=tunnels,
        )
        assert "Site A" in output
        assert "Site B" in output
        assert "vpn-down" in output

    def test_no_tunnels(self):
        output = render_svg(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            vpn_tunnels=None,
        )
        assert 'class="vpn-tunnels"' not in output

    def test_vpn_no_gateway(self):
        tunnel = VpnTunnel(
            name="Remote",
            vpn_type="sdwan-mesh-tunnel",
            remote_subnets=(),
            ifname=None,
            enabled=True,
            up=True,
            gateway_mac=None,
        )
        output = render_svg(
            [Edge("Switch1", "Switch2")],
            node_types={"Switch1": "switch", "Switch2": "switch"},
            vpn_tunnels=[tunnel],
        )
        assert 'class="vpn-tunnels"' not in output


class TestIsoVpnRendering:
    def test_single_tunnel_isometric(self):
        tunnel = VpnTunnel(
            name="Remote Site",
            vpn_type="sdwan-mesh-tunnel",
            remote_subnets=("10.0.0.0/24",),
            ifname="wgsts1000",
            enabled=True,
            up=True,
            gateway_mac=None,
        )
        output = render_svg_isometric(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            vpn_tunnels=[tunnel],
        )
        assert 'class="vpn-tunnels"' in output
        assert "Remote Site" in output

    def test_tunnel_down_isometric(self):
        tunnel = VpnTunnel(
            name="Site Down",
            vpn_type="sdwan-mesh-tunnel",
            remote_subnets=(),
            ifname=None,
            enabled=True,
            up=False,
            gateway_mac=None,
        )
        output = render_svg_isometric(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            vpn_tunnels=[tunnel],
        )
        assert "(DOWN)" in output
