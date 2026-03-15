"""Tests for orthogonal SVG label and data-attribute behavior."""

import unifi_topology.render.svg as svg_module
from unifi_topology.model.topology import Edge


def test_render_svg_escapes_edge_labels():
    output = svg_module.render_svg(
        [Edge("A", "B", label="Port 1 <-> Port 2")],
        node_types={"A": "gateway", "B": "switch"},
    )
    assert "&lt;-&gt;" in output


def test_render_svg_compacts_device_labels():
    output = svg_module.render_svg(
        [Edge("A", "B", label="Switch A: Port 2 <-> Switch B: Port 5")],
        node_types={"A": "gateway", "B": "switch"},
    )
    assert 'class="node-port"' in output
    assert "Switch A Port 2" in output
    assert ">5</tspan>" in output


def test_render_svg_orders_upstream_label():
    output = svg_module.render_svg(
        [Edge("Parent", "Child", label="Child: Port 1 <-> Parent: Port 2")],
        node_types={"Parent": "switch", "Child": "switch"},
    )
    assert "Parent Port 2 &lt;-&gt; Port 1" in output


def test_render_svg_moves_client_label_into_node():
    output = svg_module.render_svg(
        [Edge("Switch", "Client", label="Switch: Port 5 <-> Client")],
        node_types={"Switch": "switch", "Client": "client"},
    )
    assert 'class="node-port"' in output
    assert "Switch: Port 5" in output
    assert 'text-anchor="middle" fill="#555">Port 5' not in output


def test_render_svg_wraps_client_label():
    output = svg_module.render_svg(
        [Edge("Switch", "Client", label="Switch: Port 5 (very long uplink name)")],
        node_types={"Switch": "switch", "Client": "client"},
    )
    assert "<tspan" in output


def test_render_svg_prefixes_upstream_for_port_only_label():
    output = svg_module.render_svg(
        [Edge("Switch A", "Switch B", label="Port 1 <-> Port 2")],
        node_types={"Switch A": "switch", "Switch B": "switch"},
    )
    assert "Switch A Port 1" in output


def test_render_svg_client_label_without_arrow():
    output = svg_module.render_svg(
        [Edge("Switch", "Client", label="Switch: Port 3")],
        node_types={"Switch": "switch", "Client": "client"},
    )
    assert "Switch: Port 3" in output


def test_render_svg_client_label_left_side():
    output = svg_module.render_svg(
        [Edge("Client", "Switch", label="Switch: Port 4")],
        node_types={"Switch": "switch", "Client": "client"},
    )
    assert "Switch: Port 4" in output


def test_render_svg_adds_edge_data_attributes():
    output = svg_module.render_svg(
        [Edge("Gateway", "Switch")],
        node_types={"Gateway": "gateway", "Switch": "switch"},
    )
    assert 'data-edge-left="Gateway"' in output
    assert 'data-edge-right="Switch"' in output


def test_render_svg_escapes_edge_data_attributes():
    output = svg_module.render_svg(
        [Edge('Node "A"', "Node <B>")],
        node_types={'Node "A"': "gateway", "Node <B>": "switch"},
    )
    assert 'data-edge-left="Node &quot;A&quot;"' in output
    assert 'data-edge-right="Node &lt;B&gt;"' in output
