"""Tests for dual SVG output rendering."""

from tests.render_dual_helpers import basic_edges, basic_node_types
from unifi_topology.render.svg import render_dual
from unifi_topology.render.svg_theme import SvgOptions


def test_render_dual_returns_both_keys():
    result = render_dual(
        basic_edges(),
        node_types=basic_node_types(),
        vlan_names={1: "LAN", 10: "IoT"},
    )
    assert "physical" in result
    assert "vlan" in result
    assert result["physical"] is not None
    assert result["vlan"] is not None


def test_render_dual_physical_is_valid_svg():
    result = render_dual(
        basic_edges(),
        node_types=basic_node_types(),
        vlan_names={1: "LAN", 10: "IoT"},
    )
    physical = result["physical"]
    assert physical is not None
    assert physical.startswith("<svg")
    assert physical.strip().endswith("</svg>")


def test_render_dual_physical_has_no_groups():
    result = render_dual(
        basic_edges(),
        node_types=basic_node_types(),
        vlan_names={1: "LAN", 10: "IoT"},
    )
    physical = result["physical"]
    assert physical is not None
    assert 'class="group-boundary"' not in physical


def test_render_dual_isometric():
    result = render_dual(
        basic_edges(),
        node_types=basic_node_types(),
        vlan_names={1: "LAN", 10: "IoT"},
        isometric=True,
    )
    physical = result["physical"]
    vlan_svg = result["vlan"]
    assert physical is not None
    assert vlan_svg is not None
    assert "iso-node-gateway" in physical
    assert "iso-node-gateway" in vlan_svg


def test_render_dual_both_contain_same_nodes():
    node_types = basic_node_types()
    result = render_dual(
        basic_edges(),
        node_types=node_types,
        vlan_names={1: "LAN", 10: "IoT"},
    )
    physical = result["physical"]
    vlan_svg = result["vlan"]
    assert physical is not None
    assert vlan_svg is not None
    for node_name in node_types:
        assert node_name in physical
        assert node_name in vlan_svg


def test_render_dual_options_preserved():
    result = render_dual(
        basic_edges(),
        node_types=basic_node_types(),
        options=SvgOptions(width=800, height=600),
        vlan_names={1: "LAN", 10: "IoT"},
    )
    physical = result["physical"]
    vlan_svg = result["vlan"]
    assert physical is not None
    assert vlan_svg is not None
    assert 'width="800"' in physical
    assert 'width="800"' in vlan_svg
