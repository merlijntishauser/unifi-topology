"""Compatibility tests for unknown uplink edge behavior."""

from __future__ import annotations

from types import SimpleNamespace

from unifi_topology.model.edges import build_edges
from unifi_topology.model.topology_coerce import coerce_device


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
