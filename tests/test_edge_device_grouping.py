"""Tests for edge device-type and primary VLAN helpers."""

from __future__ import annotations

from tests.edge_discovery_helpers import make_device
from unifi_topology.model.edges import _primary_vlan_for_node, group_devices_by_type
from unifi_topology.model.helpers import normalize_mac
from unifi_topology.model.topology import Edge


def test_group_devices_by_type_all_types():
    gw = make_device("GW", "aa", device_type="gateway")
    sw = make_device("SW", "bb", device_type="usw")
    ap = make_device("AP", "cc", device_type="uap")
    other = make_device("Cam", "dd", device_type="camera")
    groups = group_devices_by_type([gw, sw, ap, other])
    assert normalize_mac("aa") in groups["gateway"]
    assert normalize_mac("bb") in groups["switch"]
    assert normalize_mac("cc") in groups["ap"]
    assert normalize_mac("dd") in groups["other"]


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
