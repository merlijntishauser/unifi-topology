"""Tests for SVG group rendering."""

import unifi_topology.render.svg as svg_module
import unifi_topology.render.svg_isometric as svg_iso_module
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
