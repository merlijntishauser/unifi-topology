"""Tests for orthogonal SVG grouped layout fallbacks."""

import unifi_topology.render.svg as svg_module
from unifi_topology.model.topology import Edge


def test_render_svg_physical_ignores_groups():
    edges = [Edge("A", "B")]
    node_types = {"A": "gateway", "B": "switch"}
    groups = {"Core": ["A", "B"]}
    output = svg_module.render_svg(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="physical"),
        groups=groups,
    )
    assert 'class="group-boundary"' not in output


def test_render_svg_groups_handles_empty_groups():
    edges = [Edge("A", "B")]
    node_types = {"A": "gateway", "B": "switch"}
    output = svg_module.render_svg(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="grouped"),
        groups={},
    )
    assert output.startswith("<svg")


def test_render_svg_groups_handles_ungrouped_nodes():
    edges = [Edge("A", "B"), Edge("A", "C")]
    node_types = {"A": "gateway", "B": "switch", "C": "ap"}
    groups = {"Core": ["A"]}
    output = svg_module.render_svg(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="grouped"),
        groups=groups,
    )
    assert output.startswith("<svg")
    assert "B" in output
    assert "C" in output


def test_render_svg_groups_none_works():
    edges = [Edge("A", "B")]
    node_types = {"A": "gateway", "B": "switch"}
    output = svg_module.render_svg(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="grouped"),
        groups=None,
    )
    assert output.startswith("<svg")
    assert 'class="group-boundary"' not in output
