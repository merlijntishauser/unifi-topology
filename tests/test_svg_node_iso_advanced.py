"""Tests for advanced SVG node and isometric helper behavior."""

from __future__ import annotations

from unifi_topology.model.topology import Edge
from unifi_topology.render.svg import render_svg
from unifi_topology.render.svg_isometric import render_svg_isometric
from unifi_topology.render.svg_theme import SvgOptions


class TestNodeDataAttributes:
    def test_node_data_adds_attributes(self):
        output = render_svg(
            [Edge("A", "B")],
            node_types={"A": "gateway", "B": "switch"},
            node_data={"A": {"data-custom": "value"}},
        )
        assert 'data-custom="value"' in output

    def test_node_data_merges_class(self):
        output = render_svg(
            [Edge("A", "B")],
            node_types={"A": "gateway", "B": "switch"},
            node_data={"A": {"class": "highlighted"}},
        )
        assert 'class="unm-node highlighted"' in output


class TestIsoGroupBounds:
    def test_single_node_group(self):
        edges = [Edge("Gateway", "Switch")]
        node_types = {"Gateway": "gateway", "Switch": "switch"}
        groups = {"Core": ["Gateway"]}
        output = render_svg_isometric(
            edges,
            node_types=node_types,
            options=SvgOptions(layout_mode="grouped"),
            groups=groups,
        )
        assert 'class="group-boundary"' in output

    def test_empty_group_skipped(self):
        edges = [Edge("A", "B")]
        node_types = {"A": "gateway", "B": "switch"}
        groups = {"Empty": ["NonExistent"]}
        output = render_svg_isometric(
            edges,
            node_types=node_types,
            options=SvgOptions(layout_mode="grouped"),
            groups=groups,
        )
        assert output.startswith("<svg")


class TestIsoPoEPositioning:
    def test_poe_elbow_path(self):
        edges = [Edge("Root", "B", poe=True), Edge("Root", "C")]
        node_types = {"Root": "gateway", "B": "switch", "C": "switch"}
        output = render_svg_isometric(edges, node_types=node_types)
        assert "iso-poe-bolt" in output

    def test_poe_straight_path(self):
        edges = [Edge("A", "B", poe=True)]
        node_types = {"A": "gateway", "B": "switch"}
        output = render_svg_isometric(edges, node_types=node_types)
        assert "iso-poe-bolt" in output
