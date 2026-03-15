"""Tests for isometric SVG VPN rendering."""

from __future__ import annotations

from tests.svg_vpn_render_helpers import gateway_edges, gateway_node_types, vpn_tunnel
from unifi_topology.render.svg_isometric import render_svg_isometric


class TestIsoVpnRendering:
    def test_single_tunnel_isometric(self):
        output = render_svg_isometric(
            gateway_edges(),
            node_types=gateway_node_types(),
            vpn_tunnels=[vpn_tunnel()],
        )

        assert 'class="vpn-tunnels"' in output
        assert "Remote Site" in output

    def test_tunnel_down_isometric(self):
        output = render_svg_isometric(
            gateway_edges(),
            node_types=gateway_node_types(),
            vpn_tunnels=[vpn_tunnel(name="Site Down", remote_subnets=(), ifname=None, up=False)],
        )
        assert "(DOWN)" in output
