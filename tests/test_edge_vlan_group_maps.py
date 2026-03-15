"""Tests for edge VLAN grouping helpers."""

from __future__ import annotations

from tests.edge_discovery_helpers import make_device
from unifi_topology.model.edges import (
    _primary_vlan_for_node,
    group_devices_by_type,
    group_nodes_by_vlan,
)
from unifi_topology.model.topology import Edge


def test_group_devices_by_type_all_types():
    gw = make_device("GW", "aa", device_type="gateway")
    sw = make_device("SW", "bb", device_type="usw")
    ap = make_device("AP", "cc", device_type="uap")
    other = make_device("Cam", "dd", device_type="camera")
    groups = group_devices_by_type([gw, sw, ap, other])
    assert "GW" in groups["gateway"]
    assert "SW" in groups["switch"]
    assert "AP" in groups["ap"]
    assert "Cam" in groups["other"]


def test_group_devices_by_type_empty():
    assert group_devices_by_type([]) == {"gateway": [], "switch": [], "ap": [], "other": []}


def test_primary_vlan_for_node_uses_active_vlans():
    edges = [Edge("A", "B", active_vlans=(10, 20), vlans=(10, 20, 30))]
    assert _primary_vlan_for_node("A", edges) == 10


def test_primary_vlan_for_node_falls_back_to_vlans():
    assert _primary_vlan_for_node("A", [Edge("A", "B", vlans=(30, 40))]) == 30


def test_primary_vlan_for_node_no_match():
    assert _primary_vlan_for_node("C", [Edge("A", "B")]) is None


def test_primary_vlan_for_node_no_vlans():
    assert _primary_vlan_for_node("A", [Edge("A", "B")]) is None


def test_primary_vlan_for_node_right_side():
    assert _primary_vlan_for_node("B", [Edge("A", "B", vlans=(50,))]) == 50


def test_group_nodes_by_vlan_basic():
    edges = [
        Edge("A", "B", vlans=(10,), active_vlans=(10,)),
        Edge("B", "C", vlans=(20,), active_vlans=(20,)),
    ]
    groups, order, vlan_ids = group_nodes_by_vlan(edges)
    assert groups
    assert order
    all_nodes = set()
    for node_list in groups.values():
        all_nodes.update(node_list)
    assert {"A", "B", "C"} == all_nodes


def test_group_nodes_by_vlan_with_names():
    groups, _order, vlan_ids = group_nodes_by_vlan(
        [Edge("A", "B", vlans=(10,), active_vlans=(10,))],
        vlan_names={10: "Management"},
    )
    assert "Management" in groups
    assert vlan_ids["Management"] == 10


def test_group_nodes_by_vlan_unassigned():
    groups, order, _vlan_ids = group_nodes_by_vlan([Edge("A", "B")])
    assert "Unassigned" in groups
    assert "A" in groups["Unassigned"]
    assert "B" in groups["Unassigned"]
    assert order[-1] == "Unassigned"


def test_group_nodes_by_vlan_default_name():
    groups, _order, vlan_ids = group_nodes_by_vlan(
        [Edge("A", "B", vlans=(42,), active_vlans=(42,))]
    )
    assert "VLAN 42" in groups
    assert vlan_ids["VLAN 42"] == 42


def test_group_nodes_by_vlan_mixed():
    edges = [
        Edge("A", "B", vlans=(10,), active_vlans=(10,)),
        Edge("C", "D"),
    ]
    groups, _order, _vlan_ids = group_nodes_by_vlan(edges)
    assert "Unassigned" in groups
    assert "C" in groups["Unassigned"]
    assert "D" in groups["Unassigned"]


def test_group_nodes_by_vlan_order():
    edges = [
        Edge("A", "B", vlans=(20,), active_vlans=(20,)),
        Edge("C", "D", vlans=(10,), active_vlans=(10,)),
        Edge("E", "F"),
    ]
    _groups, order, vlan_ids = group_nodes_by_vlan(edges)
    vlan_order = [value for value in order if value != "Unassigned"]
    assert vlan_ids[vlan_order[0]] < vlan_ids[vlan_order[1]]
    assert order[-1] == "Unassigned"


def test_group_nodes_by_vlan_empty_edges():
    groups, order, vlan_ids = group_nodes_by_vlan([])
    assert groups == {}
    assert order == []
    assert vlan_ids == {}
