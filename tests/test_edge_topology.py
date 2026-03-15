"""Tests for edge topology, grouping, and VLAN helpers."""

from __future__ import annotations

from unifi_topology.model.edges import (
    _primary_vlan_for_node,
    build_topology,
    build_tree_edges_by_topology,
    enrich_edges_with_active_vlans,
    group_devices_by_type,
    group_nodes_by_vlan,
)
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import Device, Edge, PortInfo, UplinkInfo


def _make_device(
    name: str,
    mac: str,
    *,
    device_type: str = "switch",
    lldp_info: list[LLDPEntry] | None = None,
    port_table: list[PortInfo] | None = None,
    poe_ports: dict[int, bool] | None = None,
    uplink: UplinkInfo | None = None,
    last_uplink: UplinkInfo | None = None,
) -> Device:
    return Device(
        name=name,
        model_name="",
        model="",
        mac=mac,
        ip="",
        type=device_type,
        lldp_info=lldp_info or [],
        port_table=port_table or [],
        poe_ports=poe_ports or {},
        uplink=uplink,
        last_uplink=last_uplink,
    )


def test_build_tree_edges_simple_chain():
    edges = [Edge("Gateway", "Switch"), Edge("Switch", "AP")]
    result = build_tree_edges_by_topology(edges, ["Gateway"])
    assert len(result) == 2
    left_right = [(edge.left, edge.right) for edge in result]
    assert ("Gateway", "Switch") in left_right
    assert ("Switch", "AP") in left_right


def test_build_tree_edges_preserves_edge_properties():
    edges = [
        Edge(
            "Gateway",
            "Switch",
            label="Port 1 <-> Port 2",
            poe=True,
            speed=1000,
            vlans=(10, 20),
            is_trunk=True,
        )
    ]
    result = build_tree_edges_by_topology(edges, ["Gateway"])
    assert len(result) == 1
    assert result[0].left == "Gateway"
    assert result[0].right == "Switch"
    assert result[0].label == "Port 1 <-> Port 2"
    assert result[0].poe is True
    assert result[0].speed == 1000
    assert result[0].vlans == (10, 20)
    assert result[0].is_trunk is True


def test_build_tree_edges_gateway_not_in_edges():
    assert build_tree_edges_by_topology([Edge("A", "B")], ["Missing"]) == []


def test_build_tree_edges_multiple_gateways():
    edges = [Edge("GW1", "Switch"), Edge("GW2", "AP")]
    assert len(build_tree_edges_by_topology(edges, ["GW1", "GW2"])) == 2


def test_enrich_edges_with_active_vlans_basic():
    edges = [Edge("Switch", "AP", vlans=(10, 20, 30))]
    client_edges = [
        Edge("Switch", "Client1", active_vlans=(10,)),
        Edge("AP", "Client2", active_vlans=(20,)),
    ]
    result = enrich_edges_with_active_vlans(edges, client_edges)
    assert len(result) == 1
    assert result[0].active_vlans == (10, 20)


def test_enrich_edges_with_active_vlans_no_overlap():
    edges = [Edge("Switch", "AP", vlans=(10, 20))]
    client_edges = [Edge("Switch", "Client1", active_vlans=(99,))]
    assert enrich_edges_with_active_vlans(edges, client_edges)[0].active_vlans == ()


def test_enrich_edges_with_active_vlans_empty_clients():
    edges = [Edge("Switch", "AP", vlans=(10, 20))]
    assert enrich_edges_with_active_vlans(edges, [])[0].active_vlans == ()


def test_enrich_edges_preserves_other_fields():
    edges = [
        Edge(
            "Switch",
            "AP",
            label="Port 1",
            poe=True,
            wireless=True,
            speed=1000,
            channel=36,
            vlans=(10,),
            is_trunk=False,
        )
    ]
    result = enrich_edges_with_active_vlans(edges, [Edge("Switch", "Client1", active_vlans=(10,))])
    assert result[0].label == "Port 1"
    assert result[0].poe is True
    assert result[0].wireless is True
    assert result[0].speed == 1000
    assert result[0].channel == 36
    assert result[0].is_trunk is False
    assert result[0].active_vlans == (10,)


def test_group_devices_by_type_all_types():
    gw = _make_device("GW", "aa", device_type="gateway")
    sw = _make_device("SW", "bb", device_type="usw")
    ap = _make_device("AP", "cc", device_type="uap")
    other = _make_device("Cam", "dd", device_type="camera")
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


def test_build_topology_with_gateways():
    gateway = _make_device("Gateway", "aa", device_type="gateway")
    switch = _make_device("Switch", "bb", lldp_info=[LLDPEntry("aa", "Port 1")])
    result = build_topology(
        [gateway, switch],
        include_ports=True,
        only_unifi=True,
        gateways=["Gateway"],
    )
    assert len(result.raw_edges) == 1
    assert len(result.tree_edges) == 1


def test_build_topology_without_gateways():
    gateway = _make_device("Gateway", "aa", device_type="gateway")
    switch = _make_device("Switch", "bb", lldp_info=[LLDPEntry("aa", "Port 1")])
    result = build_topology(
        [gateway, switch],
        include_ports=False,
        only_unifi=True,
        gateways=[],
    )
    assert len(result.raw_edges) == 1
    assert result.tree_edges == []
