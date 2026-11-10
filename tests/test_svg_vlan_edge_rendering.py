"""Tests for VLAN SVG edge rendering behavior."""

from __future__ import annotations

from unifi_topology.model.topology import Edge
from unifi_topology.render.svg import render_svg
from unifi_topology.render.svg_iso_edges import _render_iso_vlan_striped_edge
from unifi_topology.render.svg_theme import DEFAULT_THEME


class TestVlanStripedEdgeRendering:
    def test_edge_with_active_vlans(self):
        edges = [Edge("A", "B", vlans=(10, 20), active_vlans=(10,))]
        output = render_svg(
            edges,
            node_types={"A": "gateway", "B": "switch"},
        )
        assert 'data-vlans="10,20"' in output or 'data-active-vlans="10"' in output

    def test_edge_with_multiple_active_vlans(self):
        edges = [Edge("A", "B", active_vlans=(10, 20, 30))]
        output = render_svg(
            edges,
            node_types={"A": "gateway", "B": "switch"},
        )
        assert "<path" in output


class TestIsoVlanStripedEdge:
    def test_empty_vlans(self):
        lines = []
        _render_iso_vlan_striped_edge(
            lines, "M 0 0 L 100 100", (), DEFAULT_THEME, 4, False, "", 1.0
        )
        assert lines == []

    def test_single_vlan(self):
        lines = []
        _render_iso_vlan_striped_edge(
            lines, "M 0 0 L 100 100", (10,), DEFAULT_THEME, 4, False, "", 1.0
        )
        assert len(lines) >= 2

    def test_wireless_dash_pattern(self):
        lines = []
        _render_iso_vlan_striped_edge(
            lines, "M 0 0 L 100 100", (10,), DEFAULT_THEME, 4, True, "", 1.0
        )
        assert any("stroke-dasharray" in line for line in lines)

    def test_reduced_opacity(self):
        lines = []
        _render_iso_vlan_striped_edge(
            lines, "M 0 0 L 100 100", (10,), DEFAULT_THEME, 4, False, "", 0.5
        )
        assert any('opacity="0.5"' in line for line in lines)


def test_vlan_endpoint_markers_are_drawn_outside_node_boxes():
    import re

    edges = [
        Edge("gw", "sw", vlans=(1, 10, 20), active_vlans=(1, 10, 20)),
        Edge("sw", "cam", vlans=(10,), active_vlans=(10,), poe=True),
    ]
    output = render_svg(edges, node_types={"gw": "gateway", "sw": "switch", "cam": "client"})

    def boxes(pattern: str) -> list[tuple[float, ...]]:
        return [tuple(float(value) for value in match) for match in re.findall(pattern, output)]

    number = r'"([\d.]+)"'
    geometry = f"x={number} y={number} width={number} height={number}"
    markers = boxes(f"<rect {geometry} [^>]*data-vlan=")
    nodes = boxes(f'<rect {geometry} rx="6" ry="6" fill="url\\(#node-')
    assert len(markers) == 4
    assert len(nodes) == 3
    for mx, my, mw, mh in markers:
        for nx, ny, nw, nh in nodes:
            overlaps = mx < nx + nw and nx < mx + mw and my < ny + nh and ny < my + mh
            assert not overlaps
