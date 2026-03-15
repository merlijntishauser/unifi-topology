"""Compatibility-focused tests for low-level WAN helpers."""

from __future__ import annotations

from unifi_topology.model.topology import PortInfo
from unifi_topology.model.wan import _find_wan_port_by_assignment, _normalize_wan_speed


def test_normalize_wan_speed_converts_gbps_to_mbps():
    assert _normalize_wan_speed(10) == 10000
    assert _normalize_wan_speed(1) == 1000
    assert _normalize_wan_speed(100) == 100000
    assert _normalize_wan_speed(25) == 25000


def test_normalize_wan_speed_preserves_mbps():
    assert _normalize_wan_speed(1000) == 1000
    assert _normalize_wan_speed(10000) == 10000
    assert _normalize_wan_speed(100000) == 100000


def test_normalize_wan_speed_handles_none_and_zero():
    assert _normalize_wan_speed(None) is None
    assert _normalize_wan_speed(0) == 0


def test_find_wan_port_by_assignment_finds_wan():
    port_table = [
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
    ]
    result = _find_wan_port_by_assignment(port_table, "WAN")
    assert result is not None
    assert result.port_idx == 5


def test_find_wan_port_by_assignment_finds_wan2():
    port_table = [
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
    ]
    result = _find_wan_port_by_assignment(port_table, "WAN2")
    assert result is not None
    assert result.port_idx == 7


def test_find_wan_port_by_assignment_returns_none_when_not_found():
    port_table = [
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
    ]
    assert _find_wan_port_by_assignment(port_table, "WAN") is None
