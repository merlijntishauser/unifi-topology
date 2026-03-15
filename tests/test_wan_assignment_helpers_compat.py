"""Compatibility-focused tests for WAN port assignment helpers."""

from __future__ import annotations

from unifi_topology.model.topology import PortInfo
from unifi_topology.model.wan import _find_wan_port_by_assignment


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
