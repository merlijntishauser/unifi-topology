"""Compatibility tests for edge port helper behavior."""

from __future__ import annotations

from types import SimpleNamespace

from unifi_topology.model.edges import (
    _port_speed_by_idx,
    _resolve_port_idx_from_lldp,
    _uplink_name,
    build_edges,
)
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import PortInfo, UplinkInfo
from unifi_topology.model.topology_coerce import coerce_device


def test_build_edges_resolves_port_idx_from_ifname():
    lldp = SimpleNamespace(
        chassis_id="bb",
        local_port_idx=None,
        local_port_name="eth1",
        port_id="Port 1",
        port_desc=None,
    )
    device = SimpleNamespace(
        name="Switch A",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[lldp],
        port_table=[{"port_idx": 2, "ifname": "eth1", "poe_enable": True}],
    )
    neighbor = SimpleNamespace(
        name="Switch B",
        model_name="",
        model="",
        mac="bb",
        ip="",
        type="switch",
        lldp_info=[],
        port_table=[],
    )
    edges = build_edges([coerce_device(device), coerce_device(neighbor)], include_ports=True)
    assert edges[0].label == "Switch A: Port 2 <-> Switch B: ?"


def test_resolve_port_idx_matches_port_name():
    lldp = LLDPEntry(chassis_id="bb", port_id="Port 3", local_port_name="Port 3")
    port_table = [
        PortInfo(
            port_idx=3,
            name="Port 3",
            ifname=None,
            speed=None,
            aggregation_group=None,
            port_poe=False,
            poe_enable=False,
            poe_good=False,
            poe_power=None,
        )
    ]
    assert _resolve_port_idx_from_lldp(lldp, port_table) == 3


def test_resolve_port_idx_matches_port_number():
    lldp = LLDPEntry(chassis_id="bb", port_id="Port 9", local_port_name="Port 9")
    port_table = [
        PortInfo(
            port_idx=9,
            name="Uplink",
            ifname=None,
            speed=None,
            aggregation_group=None,
            port_poe=False,
            poe_enable=False,
            poe_good=False,
            poe_power=None,
        )
    ]
    assert _resolve_port_idx_from_lldp(lldp, port_table) == 9


def test_uplink_name_prefers_name_over_mac():
    uplink = UplinkInfo(mac="aa", name="Core Switch", port=None)
    assert _uplink_name(uplink, {}, only_unifi=True) == "Core Switch"


def test_port_speed_by_idx_reads_speed():
    ports = [
        PortInfo(
            port_idx=1,
            name=None,
            ifname=None,
            speed=1000,
            aggregation_group=None,
            port_poe=False,
            poe_enable=False,
            poe_good=False,
            poe_power=None,
        )
    ]
    assert _port_speed_by_idx(ports, 1) == 1000
