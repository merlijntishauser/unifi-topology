"""Tests for VLAN-specific dual SVG rendering."""

from tests.render_dual_helpers import basic_edges, basic_node_types
from unifi_topology.model.topology import Edge
from unifi_topology.render.svg import render_dual


def test_render_dual_vlan_contains_group_boundaries():
    result = render_dual(
        basic_edges(),
        node_types=basic_node_types(),
        vlan_names={1: "LAN", 10: "IoT"},
    )
    vlan_svg = result["vlan"]
    assert vlan_svg is not None
    assert 'class="group-boundary"' in vlan_svg
    assert "LAN" in vlan_svg or "IoT" in vlan_svg


def test_render_dual_no_vlan_data_returns_none():
    result = render_dual(
        basic_edges(),
        node_types=basic_node_types(),
    )
    assert result["physical"] is not None
    assert result["vlan"] is None


def test_render_dual_empty_vlan_names_returns_none():
    result = render_dual(
        basic_edges(),
        node_types=basic_node_types(),
        vlan_names={},
    )
    assert result["vlan"] is None


def test_render_dual_vlan_node_map_override():
    edges = [Edge("A", "B"), Edge("B", "C")]
    node_types = {"A": "gateway", "B": "switch", "C": "ap"}
    result = render_dual(
        edges,
        node_types=node_types,
        vlan_node_map={"A": 1, "B": 1, "C": 20},
        vlan_names={1: "Management", 20: "Guest"},
    )
    vlan_svg = result["vlan"]
    assert vlan_svg is not None
    assert "Management" in vlan_svg
    assert "Guest" in vlan_svg


def test_render_dual_vlan_node_map_unassigned():
    edges = [Edge("A", "B")]
    node_types = {"A": "gateway", "B": "switch"}
    result = render_dual(
        edges,
        node_types=node_types,
        vlan_node_map={"A": 1, "B": None},
        vlan_names={1: "LAN"},
    )
    vlan_svg = result["vlan"]
    assert vlan_svg is not None
    assert "Unassigned" in vlan_svg


def test_render_dual_vlan_node_map_without_names():
    edges = [Edge("A", "B")]
    node_types = {"A": "gateway", "B": "switch"}
    result = render_dual(
        edges,
        node_types=node_types,
        vlan_node_map={"A": 5, "B": 5},
    )
    vlan_svg = result["vlan"]
    assert vlan_svg is not None
    assert "VLAN 5" in vlan_svg
