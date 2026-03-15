"""Tests for isometric SVG group rendering."""

import unifi_topology.render.svg as svg_module
import unifi_topology.render.svg_isometric as svg_iso_module
from unifi_topology.model.topology import Edge


def test_render_svg_isometric_groups():
    edges = [Edge("A", "B")]
    node_types = {"A": "gateway", "B": "switch"}
    groups = {"Core": ["A", "B"]}
    output = svg_iso_module.render_svg_isometric(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="grouped"),
        groups=groups,
    )
    assert 'class="group-boundary"' in output
    assert '<polygon class="group-boundary"' in output


def test_render_svg_isometric_physical_ignores_groups():
    edges = [Edge("A", "B")]
    node_types = {"A": "gateway", "B": "switch"}
    groups = {"Core": ["A", "B"]}
    output = svg_iso_module.render_svg_isometric(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="physical"),
        groups=groups,
    )
    assert 'class="group-boundary"' not in output
