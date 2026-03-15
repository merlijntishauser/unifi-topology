"""Tests for advanced SVG WAN and VPN rendering behavior."""

from __future__ import annotations

from unifi_topology.model.topology import Edge, VpnTunnel, WanInfo, WanInterface
from unifi_topology.render.svg import render_svg
from unifi_topology.render.svg_isometric import render_svg_isometric


class TestWanUpstreamRendering:
    def test_single_wan(self):
        wan = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        wan_info = WanInfo(wan1=wan, wan2=None)
        output = render_svg(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            wan_info=wan_info,
        )
        assert 'class="wan-upstream"' in output
        assert "1GbE" in output or "1.2.3.4" in output

    def test_dual_wan(self):
        wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        wan2 = WanInterface(port_idx=9, link_speed=100, ip_address="5.6.7.8", enabled=True)
        wan_info = WanInfo(wan1=wan1, wan2=wan2)
        output = render_svg(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            wan_info=wan_info,
        )
        assert "WAN1" in output or "1.2.3.4" in output
        assert "WAN2" in output or "5.6.7.8" in output

    def test_wan_with_label(self):
        wan = WanInterface(
            port_idx=1,
            link_speed=1000,
            ip_address="1.2.3.4",
            enabled=True,
            label="Fiber",
        )
        wan_info = WanInfo(wan1=wan, wan2=None)
        output = render_svg(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            wan_info=wan_info,
        )
        assert "Fiber" in output

    def test_no_wan_info(self):
        output = render_svg(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            wan_info=None,
        )
        assert 'class="wan-upstream"' not in output

    def test_wan_no_gateway(self):
        wan = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        wan_info = WanInfo(wan1=wan, wan2=None)
        output = render_svg(
            [Edge("Switch1", "Switch2")],
            node_types={"Switch1": "switch", "Switch2": "switch"},
            wan_info=wan_info,
        )
        assert 'class="wan-upstream"' not in output


class TestIsoWanUpstreamRendering:
    def test_single_wan_isometric(self):
        wan = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        wan_info = WanInfo(wan1=wan, wan2=None)
        output = render_svg_isometric(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            wan_info=wan_info,
        )
        assert 'class="wan-upstream"' in output

    def test_wan_with_disabled_wan2(self):
        wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        wan2 = WanInterface(port_idx=9, link_speed=None, ip_address=None, enabled=False)
        wan_info = WanInfo(wan1=wan1, wan2=wan2)
        output = render_svg_isometric(
            [Edge("Gateway", "Switch")],
            node_types={"Gateway": "gateway", "Switch": "switch"},
            wan_info=wan_info,
        )
        assert "disabled" in output.lower() or "WAN2" in output


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
