"""Tests for orthogonal SVG group boundary rendering."""

import unifi_topology.render.svg as svg_module
from unifi_topology.model.topology import Edge


def test_render_svg_groups_creates_boundaries():
    edges = [Edge("A", "B"), Edge("A", "C")]
    node_types = {"A": "gateway", "B": "switch", "C": "ap"}
    groups = {"Core": ["A", "B"], "Wireless": ["C"]}
    output = svg_module.render_svg(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="grouped"),
        groups=groups,
    )
    assert 'class="group-boundary"' in output
    assert 'class="network-group"' in output


def test_render_svg_groups_renders_labels():
    edges = [Edge("A", "B")]
    node_types = {"A": "gateway", "B": "switch"}
    groups = {"Infrastructure": ["A", "B"]}
    output = svg_module.render_svg(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="grouped"),
        groups=groups,
    )
    assert 'class="group-label"' in output
    assert "Infrastructure" in output


def test_render_svg_groups_respects_order():
    edges = [Edge("A", "B"), Edge("C", "D")]
    node_types = {"A": "gateway", "B": "switch", "C": "ap", "D": "client"}
    groups = {"Second": ["C", "D"], "First": ["A", "B"]}
    output = svg_module.render_svg(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="grouped"),
        groups=groups,
        group_order=["First", "Second"],
    )
    first_idx = output.find('data-group-name="First"')
    second_idx = output.find('data-group-name="Second"')
    assert first_idx < second_idx


def test_render_svg_groups_adds_data_group_attribute():
    edges = [Edge("A", "B")]
    node_types = {"A": "gateway", "B": "switch"}
    groups = {"Core": ["A", "B"]}
    output = svg_module.render_svg(
        edges,
        node_types=node_types,
        options=svg_module.SvgOptions(layout_mode="grouped"),
        groups=groups,
    )
    assert 'data-group="Core"' in output
