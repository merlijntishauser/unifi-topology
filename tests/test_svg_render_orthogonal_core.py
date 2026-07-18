"""Tests for orthogonal SVG core rendering behavior."""

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


def test_render_svg_handles_missing_positions(monkeypatch):
    from unifi_topology.render import _svg_render_flow

    monkeypatch.setattr(_svg_render_flow, "_layout_nodes", lambda _e, _n, _o: ({}, 0, 0))
    output = svg_module.render_svg([Edge("A", "B")], node_types={"A": "switch", "B": "switch"})
    assert 'stroke="url(#link' not in output


def test_render_svg_without_icons(monkeypatch):
    monkeypatch.setattr(
        svg_module, "_load_icons", lambda icon_set="isometric", decal_color="#1a1a1a": {}
    )
    output = svg_module.render_svg([Edge("A", "B")], node_types={"A": "switch", "B": "switch"})
    assert "<image" not in output
