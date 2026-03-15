"""Tests for VLAN SVG edge attribute helpers."""

from __future__ import annotations

from unifi_topology.model.topology import Edge
from unifi_topology.render.svg_edges import (
    _edge_opacity,
    _render_vlan_endpoint_markers,
    _vlan_data_attrs,
)
from unifi_topology.render.svg_theme import DEFAULT_THEME


class TestVlanDataAttrs:
    def test_empty_edge(self):
        edge = Edge("A", "B")
        assert _vlan_data_attrs(edge) == ""

    def test_vlans_only(self):
        edge = Edge("A", "B", vlans=(10, 20, 30))
        attrs = _vlan_data_attrs(edge)
        assert 'data-vlans="10,20,30"' in attrs

    def test_active_vlans(self):
        edge = Edge("A", "B", active_vlans=(10,))
        attrs = _vlan_data_attrs(edge)
        assert 'data-active-vlans="10"' in attrs

    def test_trunk(self):
        edge = Edge("A", "B", is_trunk=True)
        attrs = _vlan_data_attrs(edge)
        assert 'data-trunk="true"' in attrs

    def test_all_vlan_attrs(self):
        edge = Edge("A", "B", vlans=(10, 20), active_vlans=(10,), is_trunk=True)
        attrs = _vlan_data_attrs(edge)
        assert 'data-vlans="10,20"' in attrs
        assert 'data-active-vlans="10"' in attrs
        assert 'data-trunk="true"' in attrs


class TestEdgeOpacity:
    def test_infrastructure_edge(self):
        node_types = {"Switch": "switch", "AP": "ap"}
        edge = Edge("Switch", "AP")
        assert _edge_opacity(node_types, edge) == 1.0

    def test_client_edge_right(self):
        node_types = {"Switch": "switch", "Client": "client"}
        edge = Edge("Switch", "Client")
        assert _edge_opacity(node_types, edge) == 0.5

    def test_client_edge_left(self):
        node_types = {"Client": "client", "Switch": "switch"}
        edge = Edge("Client", "Switch")
        assert _edge_opacity(node_types, edge) == 0.5


class TestRenderVlanEndpointMarkers:
    def test_empty_vlans(self):
        lines = []
        _render_vlan_endpoint_markers(lines, 100, 100, (), DEFAULT_THEME)
        assert lines == []

    def test_single_vlan(self):
        lines = []
        _render_vlan_endpoint_markers(lines, 100, 100, (10,), DEFAULT_THEME)
        assert len(lines) == 1
        assert "<rect" in lines[0]
        assert 'data-vlan="10"' in lines[0]

    def test_multiple_vlans_limited(self):
        lines = []
        vlans = (10, 20, 30, 40, 50)
        _render_vlan_endpoint_markers(lines, 100, 100, vlans, DEFAULT_THEME, max_markers=4)
        assert len(lines) == 4
