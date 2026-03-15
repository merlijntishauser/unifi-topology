"""Tests for SVG group layout helpers."""

import unifi_topology.render.svg_layout as svg_layout_module
from unifi_topology.model.topology import Edge


def test_assign_nodes_to_groups():
    nodes = {"A", "B", "C"}
    groups = {"G1": ["A", "B"], "G2": ["C"]}
    result = svg_layout_module._assign_nodes_to_groups(nodes, groups)
    assert result == {"A": "G1", "B": "G1", "C": "G2"}


def test_resolve_group_order_with_order():
    groups = {"B": ["x"], "A": ["y"], "C": ["z"]}
    result = svg_layout_module._resolve_group_order(groups, ["A", "B", "C"])
    assert result == ["A", "B", "C"]


def test_resolve_group_order_without_order():
    groups = {"B": ["x"], "A": ["y"]}
    result = svg_layout_module._resolve_group_order(groups, None)
    assert result == ["A", "B"]


def test_filter_edges_for_group():
    edges = [Edge("A", "B"), Edge("A", "C"), Edge("C", "D")]
    group_nodes = {"A", "B"}
    result = svg_layout_module._filter_edges_for_group(edges, group_nodes)
    assert len(result) == 1
    assert result[0].left == "A" and result[0].right == "B"


def test_build_node_to_group_map():
    groups = {"G1": ["A", "B"], "G2": ["C"]}
    result = svg_layout_module._build_node_to_group_map(groups)
    assert result == {"A": "G1", "B": "G1", "C": "G2"}
