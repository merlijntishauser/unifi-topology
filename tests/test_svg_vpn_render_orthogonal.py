"""Tests for orthogonal SVG VPN rendering."""

from __future__ import annotations

from tests.svg_vpn_render_helpers import gateway_edges, gateway_node_types, vpn_tunnel
from unifi_topology.model.topology import Edge
from unifi_topology.render.svg import render_svg


class TestVpnRendering:
    def test_single_tunnel_up(self):
        output = render_svg(
            gateway_edges(),
            node_types=gateway_node_types(),
            vpn_tunnels=[vpn_tunnel(gateway_mac="aa:bb:cc:dd:ee:01")],
        )

        assert 'class="vpn-tunnels"' in output
        assert "Remote Site" in output
        assert "(UP)" in output

    def test_single_tunnel_down(self):
        output = render_svg(
            gateway_edges(),
            node_types=gateway_node_types(),
            vpn_tunnels=[vpn_tunnel(remote_subnets=(), ifname=None, up=False)],
        )

        assert 'class="vpn-tunnels"' in output
        assert "(DOWN)" in output

    def test_multiple_tunnels(self):
        output = render_svg(
            gateway_edges(),
            node_types=gateway_node_types(),
            vpn_tunnels=[
                vpn_tunnel(name="Site A", gateway_mac=None),
                vpn_tunnel(
                    name="Site B",
                    remote_subnets=("172.16.0.0/16",),
                    ifname="wgsts1001",
                    up=False,
                ),
            ],
        )

        assert "Site A" in output
        assert "Site B" in output
        assert "vpn-down" in output

    def test_no_tunnels(self):
        output = render_svg(
            gateway_edges(),
            node_types=gateway_node_types(),
            vpn_tunnels=None,
        )
        assert 'class="vpn-tunnels"' not in output

    def test_vpn_no_gateway(self):
        output = render_svg(
            [Edge("Switch1", "Switch2")],
            node_types={"Switch1": "switch", "Switch2": "switch"},
            vpn_tunnels=[vpn_tunnel(name="Remote")],
        )
        assert 'class="vpn-tunnels"' not in output
