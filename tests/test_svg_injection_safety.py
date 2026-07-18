"""Tests guarding SVG output against attribute injection from caller data."""

from unifi_topology.model.topology import Edge
from unifi_topology.render.svg import render_svg
from unifi_topology.render.svg_isometric import render_svg_isometric

_HOSTILE_TYPE = 'x" onload="alert(1)'


def test_render_svg_rejects_attribute_injection_via_node_type():
    output = render_svg([Edge("a", "b")], node_types={"a": _HOSTILE_TYPE})
    assert "onload" not in output


def test_render_svg_isometric_rejects_attribute_injection_via_node_type():
    output = render_svg_isometric([Edge("a", "b")], node_types={"a": _HOSTILE_TYPE})
    assert "onload" not in output


def test_render_svg_unknown_node_type_falls_back_to_other_gradient():
    output = render_svg([Edge("a", "b")], node_types={"a": "weird_type"})
    assert "url(#node-weird_type)" not in output
    assert 'fill="url(#node-other)"' in output


def test_render_svg_isometric_unknown_node_type_falls_back_to_other_gradient():
    output = render_svg_isometric([Edge("a", "b")], node_types={"a": "weird_type"})
    assert "url(#iso-node-weird_type)" not in output
    assert 'fill="url(#iso-node-other)"' in output


def test_render_svg_rejects_attribute_injection_via_node_data_keys():
    output = render_svg(
        [Edge("a", "b")],
        node_types={"a": "gateway", "b": "switch"},
        node_data={"a": {'x" onclick="evil': "1"}},
    )
    assert "onclick" not in output


def test_render_svg_keeps_valid_node_data_keys():
    output = render_svg(
        [Edge("a", "b")],
        node_types={"a": "gateway", "b": "switch"},
        node_data={"a": {"data-ip": "10.0.0.1"}},
    )
    assert 'data-ip="10.0.0.1"' in output
