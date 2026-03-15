"""Compatibility-focused topology tests for tree and topology assembly paths."""

from __future__ import annotations

from types import SimpleNamespace

from unifi_topology.model.edges import (
    _tree_edges_from_parent,
    build_topology,
    build_tree_edges_by_topology,
)
from unifi_topology.model.topology import Edge
from unifi_topology.model.topology_coerce import coerce_device


def test_build_tree_edges_returns_empty_without_gateways():
    assert build_tree_edges_by_topology([Edge("A", "B")], gateways=[]) == []


def test_build_tree_edges_no_gateways():
    assert build_tree_edges_by_topology([], []) == []


def test_build_tree_edges_gateway_not_in_adjacency():
    assert build_tree_edges_by_topology([Edge("A", "B")], ["Missing"]) == []


def test_build_topology_returns_edges():
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
    result = build_topology(
        [coerce_device(device)], include_ports=False, only_unifi=False, gateways=[]
    )
    assert result.raw_edges


def test_tree_edges_from_parent_missing_original():
    parent = {"Switch A": "Gateway"}
    assert _tree_edges_from_parent(parent, {}) == [Edge(left="Gateway", right="Switch A")]
