"""Compatibility tests for WAN2 extraction state handling."""

from __future__ import annotations

from unifi_topology.model.topology import Device, PortInfo
from unifi_topology.model.wan import extract_wan_info


def _gateway_with_dual_wan(wan2_speed: int | None = 10) -> Device:
    return Device(
        name="Gateway",
        model_name="UDM Pro Max",
        model="UDMPROMAX",
        mac="aa:bb:cc:dd:ee:ff",
        ip="85.145.111.204",
        type="udm",
        lldp_info=[],
        port_table=[
            PortInfo(
                port_idx=5,
                name="Port 5",
                ifname="eth4",
                speed=10,
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
                speed=wan2_speed,
                aggregation_group=None,
                port_poe=False,
                poe_enable=False,
                poe_good=False,
                poe_power=None,
                wan_networkconf_id="WAN2",
            ),
        ],
    )


def test_extract_wan_info_wan2_disabled_via_network_config():
    result = extract_wan_info(
        _gateway_with_dual_wan(wan2_speed=10),
        wan_enabled_map={"wan": True, "wan2": False},
    )
    assert result is not None
    assert result.wan1 is not None
    assert result.wan1.enabled is True
    assert result.wan2 is not None
    assert result.wan2.enabled is False
    assert result.wan2.link_speed == 10000


def test_extract_wan_info_wan2_enabled_via_network_config():
    result = extract_wan_info(
        _gateway_with_dual_wan(wan2_speed=10),
        wan_enabled_map={"wan": True, "wan2": True},
    )
    assert result is not None
    assert result.wan2 is not None
    assert result.wan2.enabled is True


def test_extract_wan_info_wan2_disabled_cli_override():
    result = extract_wan_info(
        _gateway_with_dual_wan(wan2_speed=10),
        wan_enabled_map={"wan": True, "wan2": True},
        wan2_disabled="true",
    )
    assert result is not None
    assert result.wan2 is not None
    assert result.wan2.enabled is False


def test_extract_wan_info_wan2_enabled_cli_override():
    result = extract_wan_info(
        _gateway_with_dual_wan(wan2_speed=10),
        wan_enabled_map={"wan": True, "wan2": False},
        wan2_disabled="false",
    )
    assert result is not None
    assert result.wan2 is not None
    assert result.wan2.enabled is True


def test_extract_wan_info_wan2_auto_fallback_to_speed():
    result = extract_wan_info(_gateway_with_dual_wan(wan2_speed=10), wan2_disabled="auto")
    assert result is not None
    assert result.wan2 is not None
    assert result.wan2.enabled is True
    result2 = extract_wan_info(_gateway_with_dual_wan(wan2_speed=None), wan2_disabled="auto")
    assert result2 is not None
    assert result2.wan2 is not None
    assert result2.wan2.enabled is False
