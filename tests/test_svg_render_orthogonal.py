"""Tests for orthogonal SVG rendering."""

import re

import unifi_topology.render.svg as svg_module
from unifi_topology.model.topology import Edge


def test_render_svg_outputs_svg_root():
    output = svg_module.render_svg([Edge("A", "B")], node_types={"A": "gateway", "B": "switch"})
    assert output.startswith("<svg")


def test_render_svg_respects_size_override():
    output = svg_module.render_svg(
        [Edge("A", "B")],
        node_types={"A": "gateway", "B": "switch"},
        options=svg_module.SvgOptions(width=800, height=600),
    )
    assert 'width="800"' in output


def test_render_svg_escapes_edge_labels():
    output = svg_module.render_svg(
        [Edge("A", "B", label="Port 1 <-> Port 2")],
        node_types={"A": "gateway", "B": "switch"},
    )
    assert "&lt;-&gt;" in output


def test_render_svg_renders_poe_icon():
    output = svg_module.render_svg(
        [Edge("A", "B", poe=True)],
        node_types={"A": "gateway", "B": "switch"},
    )
    assert "poe-bolt" in output


def test_render_svg_dashes_wireless_links():
    output = svg_module.render_svg(
        [Edge("A", "B", wireless=True)],
        node_types={"A": "gateway", "B": "switch"},
    )
    assert 'stroke-dasharray="6 4"' in output


def test_render_svg_adds_elbow_for_vertical_links():
    output = svg_module.render_svg(
        [Edge("Root", "Child")],
        node_types={"Root": "gateway", "Child": "switch"},
    )
    match = re.search(r'<path d="([^"]+)"', output)
    assert match is not None
    coords = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", match.group(1))]
    x_values = {round(x, 2) for x in coords[0::2]}
    assert len(x_values) > 1


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


def test_render_svg_handles_missing_positions(monkeypatch):
    monkeypatch.setattr(svg_module, "_layout_nodes", lambda _e, _n, _o: ({}, 0, 0))
    output = svg_module.render_svg([Edge("A", "B")], node_types={"A": "switch", "B": "switch"})
    assert 'stroke="url(#link' not in output


def test_render_svg_without_icons(monkeypatch):
    monkeypatch.setattr(
        svg_module, "_load_icons", lambda icon_set="isometric", decal_color="#1a1a1a": {}
    )
    output = svg_module.render_svg([Edge("A", "B")], node_types={"A": "switch", "B": "switch"})
    assert "<image" not in output


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
