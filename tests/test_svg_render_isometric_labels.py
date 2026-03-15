"""Tests for isometric SVG label behavior."""

import unifi_topology.render.svg_isometric as svg_iso_module
from unifi_topology.model.topology import Edge


def test_render_svg_isometric_renders_label_tile():
    output = svg_iso_module.render_svg_isometric(
        [Edge("A", "B", label="A: Port 1 <-> B: Port 2")],
        node_types={"A": "switch", "B": "switch"},
    )
    assert 'class="label-tile"' in output


def test_render_svg_isometric_client_label_without_arrow():
    output = svg_iso_module.render_svg_isometric(
        [Edge("Switch", "Client", label="Switch: Port 4")],
        node_types={"Switch": "switch", "Client": "client"},
    )
    assert "Switch: Port 4" in output


def test_render_svg_isometric_client_left_label():
    output = svg_iso_module.render_svg_isometric(
        [Edge("Client", "Switch", label="Switch: Port 2")],
        node_types={"Switch": "switch", "Client": "client"},
    )
    assert "Switch: Port 2" in output


def test_render_svg_isometric_port_prefixes_upstream():
    output = svg_iso_module.render_svg_isometric(
        [Edge("Switch", "AP", label="Port 1 <-> Port 2")],
        node_types={"Switch": "switch", "AP": "ap"},
    )
    assert "Switch: Port 1" in output
