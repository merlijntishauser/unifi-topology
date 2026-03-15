"""Compatibility tests for WAN extraction assignment behavior."""

from __future__ import annotations

from unifi_topology.model.topology import Device, PortInfo
from unifi_topology.model.wan import extract_wan_info


def test_extract_wan_info_uses_assignment():
    device = Device(
        name="Gateway",
        model_name="UDM Pro",
        model="UDMPRO",
        mac="aa:bb:cc:dd:ee:ff",
        ip="85.145.111.204",
        type="udm",
        lldp_info=[],
        port_table=[
            PortInfo(
                port_idx=1,
                name="Port 1",
                ifname="eth0",
                speed=1000,
                aggregation_group=None,
                port_poe=False,
                poe_enable=False,
                poe_good=False,
                poe_power=None,
            ),
            PortInfo(
                port_idx=5,
                name="Port 5",
                ifname="eth4",
                speed=10000,
                aggregation_group=None,
                port_poe=False,
                poe_enable=False,
                poe_good=False,
                poe_power=None,
                wan_networkconf_id="WAN",
            ),
            PortInfo(
                port_idx=7,
                name="SFP+ 2",
                ifname="eth6",
                speed=None,
                aggregation_group=None,
                port_poe=False,
                poe_enable=False,
                poe_good=False,
                poe_power=None,
                wan_networkconf_id="WAN2",
            ),
        ],
    )
    result = extract_wan_info(device, wan1_label="Odido")
    assert result is not None
    assert result.wan1 is not None
    assert result.wan1.port_idx == 5
    assert result.wan1.link_speed == 10000
    assert result.wan1.label == "Odido"
    assert result.wan2 is not None
    assert result.wan2.port_idx == 7
    assert result.wan2.enabled is False


def test_extract_wan_info_fallback_to_port_idx():
    device = Device(
        name="Gateway",
        model_name="UDM",
        model="UDM",
        mac="aa:bb:cc:dd:ee:ff",
        ip="192.168.1.1",
        type="udm",
        lldp_info=[],
        port_table=[
            PortInfo(
                port_idx=1,
                name="WAN 1",
                ifname="eth0",
                speed=2500,
                aggregation_group=None,
                port_poe=False,
                poe_enable=False,
                poe_good=False,
                poe_power=None,
            ),
        ],
    )
    result = extract_wan_info(device)
    assert result is not None
    assert result.wan1 is not None
    assert result.wan1.port_idx == 1
    assert result.wan1.link_speed == 2500
