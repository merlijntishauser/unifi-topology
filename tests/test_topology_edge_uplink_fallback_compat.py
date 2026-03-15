"""Compatibility tests for edge uplink fallback behavior."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests.topology_edge_helpers import make_device_with_uplink_no_lldp
from unifi_topology.model.edges import build_edges
from unifi_topology.model.topology import Device, UplinkInfo
from unifi_topology.model.topology_coerce import coerce_device


@pytest.fixture()
def device_with_uplink_no_lldp():
    return make_device_with_uplink_no_lldp()


def test_build_edges_uses_uplink_fallback_fixture(device_with_uplink_no_lldp):
    gateway = Device(
        name="Gateway",
        model_name="",
        model="",
        mac="bb",
        ip="",
        type="gateway",
        lldp_info=[],
    )
    device = coerce_device(device_with_uplink_no_lldp)
    edges = build_edges([gateway, device], include_ports=True)
    assert edges[0].label == "Gateway: Port 1 <-> Device: ?"


def test_build_edges_uses_uplink_fallback():
    gateway = Device(
        name="Gateway",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="gateway",
        lldp_info=[],
        poe_ports={1: True},
    )
    switch = Device(
        name="Switch",
        model_name="",
        model="",
        mac="bb",
        ip="",
        type="switch",
        lldp_info=[],
        uplink=UplinkInfo(mac="aa", name="Gateway", port=1),
    )
    edges = build_edges([gateway, switch], include_ports=True)
    assert edges[0].label == "Gateway: Port 1 <-> Switch: ?"


def test_build_edges_only_unifi_false_uses_chassis_id():
    lldp = SimpleNamespace(chassis_id="bb", local_port_idx=None, port_id="Port 1", port_desc=None)
    device = SimpleNamespace(
        name="Switch",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[lldp],
        port_table=[],
    )
    edges = build_edges([coerce_device(device)], only_unifi=False)
    assert edges[0].right == "bb"


def test_build_edges_only_unifi_skips_unknown_uplink():
    device = SimpleNamespace(
        name="Switch",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[],
        port_table=[],
        uplink_mac="cc",
    )
    assert build_edges([coerce_device(device)], only_unifi=True) == []


def test_build_edges_only_unifi_false_includes_unknown_uplink():
    device = SimpleNamespace(
        name="Switch",
        model_name="",
        model="",
        mac="aa",
        ip="",
        type="switch",
        lldp_info=[],
        port_table=[],
        uplink_mac="cc",
    )
    edges = build_edges([coerce_device(device)], only_unifi=False)
    assert (edges[0].left, edges[0].right) == ("cc", "Switch")
