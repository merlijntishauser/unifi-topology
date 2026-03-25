"""Tests for public IP (connect_request_ip) support on WAN interfaces."""

from __future__ import annotations

from unifi_topology.model.topology import Device, PortInfo, WanInfo, WanInterface
from unifi_topology.model.wan import extract_wan_info
from unifi_topology.render.svg_labels import _build_wan_label_lines


def _gateway(ip: str = "100.64.1.1", public_ip: str | None = None) -> Device:
    return Device(
        name="Gateway",
        model_name="UDM Pro",
        model="UDMPRO",
        mac="aa:bb:cc:dd:ee:ff",
        ip=ip,
        type="udm",
        lldp_info=[],
        port_table=[
            PortInfo(
                port_idx=1,
                name="WAN 1",
                ifname="eth0",
                speed=1000,
                aggregation_group=None,
                port_poe=False,
                poe_enable=False,
                poe_good=False,
                poe_power=None,
                wan_networkconf_id="WAN",
            ),
        ],
        public_ip=public_ip,
    )


class TestExtractWanPublicIp:
    def test_public_ip_propagated_to_wan1(self):
        result = extract_wan_info(_gateway(public_ip="203.0.113.5"))
        assert result is not None
        assert result.wan1 is not None
        assert result.wan1.public_ip == "203.0.113.5"

    def test_no_public_ip(self):
        result = extract_wan_info(_gateway())
        assert result is not None
        assert result.wan1 is not None
        assert result.wan1.public_ip is None

    def test_wan2_has_no_public_ip(self):
        device = Device(
            name="Gateway",
            model_name="UDM Pro",
            model="UDMPRO",
            mac="aa:bb:cc:dd:ee:ff",
            ip="100.64.1.1",
            type="udm",
            lldp_info=[],
            port_table=[
                PortInfo(
                    port_idx=1,
                    name="WAN 1",
                    ifname="eth0",
                    speed=1000,
                    aggregation_group=None,
                    port_poe=False,
                    poe_enable=False,
                    poe_good=False,
                    poe_power=None,
                    wan_networkconf_id="WAN",
                ),
                PortInfo(
                    port_idx=9,
                    name="WAN 2",
                    ifname="eth8",
                    speed=1000,
                    aggregation_group=None,
                    port_poe=False,
                    poe_enable=False,
                    poe_good=False,
                    poe_power=None,
                    wan_networkconf_id="WAN2",
                ),
            ],
            public_ip="203.0.113.5",
        )
        result = extract_wan_info(device)
        assert result is not None
        assert result.wan1 is not None
        assert result.wan1.public_ip == "203.0.113.5"
        assert result.wan2 is not None
        assert result.wan2.public_ip is None


class TestWanLabelPublicIp:
    def test_public_ip_shown_when_differs_from_wan_ip(self):
        wan = WanInterface(
            port_idx=1,
            link_speed=1000,
            ip_address="100.64.1.1",
            enabled=True,
            public_ip="203.0.113.5",
        )
        lines = _build_wan_label_lines(WanInfo(wan1=wan, wan2=None))
        assert any("203.0.113.5" in line for line in lines)
        assert not any("100.64.1.1" in line for line in lines)

    def test_wan_ip_shown_when_no_public_ip(self):
        wan = WanInterface(port_idx=1, link_speed=1000, ip_address="85.145.111.1", enabled=True)
        lines = _build_wan_label_lines(WanInfo(wan1=wan, wan2=None))
        assert any("85.145.111.1" in line for line in lines)

    def test_wan_ip_shown_when_public_ip_matches(self):
        wan = WanInterface(
            port_idx=1,
            link_speed=1000,
            ip_address="85.145.111.1",
            enabled=True,
            public_ip="85.145.111.1",
        )
        lines = _build_wan_label_lines(WanInfo(wan1=wan, wan2=None))
        assert any("85.145.111.1" in line for line in lines)

    def test_dual_wan_public_ip(self):
        wan1 = WanInterface(
            port_idx=1,
            link_speed=1000,
            ip_address="100.64.1.1",
            enabled=True,
            public_ip="203.0.113.5",
        )
        wan2 = WanInterface(port_idx=9, link_speed=100, ip_address=None, enabled=True)
        lines = _build_wan_label_lines(WanInfo(wan1=wan1, wan2=wan2))
        assert any("203.0.113.5" in line for line in lines)
        assert not any("100.64.1.1" in line for line in lines)
