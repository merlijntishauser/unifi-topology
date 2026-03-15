"""Tests for tree-edge and topology assembly behavior."""

from __future__ import annotations

from tests.edge_discovery_helpers import make_device
from unifi_topology.model.edges import build_topology, build_tree_edges_by_topology
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology import Edge


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


def test_build_topology_with_gateways():
    gateway = make_device("Gateway", "aa", device_type="gateway")
    switch = make_device("Switch", "bb", lldp_info=[LLDPEntry("aa", "Port 1")])
    result = build_topology(
        [gateway, switch],
        include_ports=True,
        only_unifi=True,
        gateways=["Gateway"],
    )
    assert len(result.raw_edges) == 1
    assert len(result.tree_edges) == 1


def test_build_topology_without_gateways():
    gateway = make_device("Gateway", "aa", device_type="gateway")
    switch = make_device("Switch", "bb", lldp_info=[LLDPEntry("aa", "Port 1")])
    result = build_topology(
        [gateway, switch],
        include_ports=False,
        only_unifi=True,
        gateways=[],
    )
    assert len(result.raw_edges) == 1
    assert result.tree_edges == []
