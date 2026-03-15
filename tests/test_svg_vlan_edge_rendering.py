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
