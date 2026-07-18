"""The isometric floor grid must share the node tile offset."""

from __future__ import annotations

import re

from unifi_topology.model.topology import Edge
from unifi_topology.render._svg_iso_layout import _iso_grid_line, _iso_layout_positions
from unifi_topology.render.svg_iso_geometry import _iso_project
from unifi_topology.render.svg_theme import SvgOptions


def _line_start(markup: str) -> tuple[float, float]:
    match = re.search(r'x1="([\d.-]+)" y1="([\d.-]+)"', markup)
    assert match
    return float(match.group(1)), float(match.group(2))


def test_grid_line_uses_node_offset_not_padding():
    edges = [Edge("Gateway", "Switch"), Edge("Switch", "AP")]
    node_types = {"Gateway": "gateway", "Switch": "switch", "AP": "ap"}
    lp = _iso_layout_positions(edges, node_types, SvgOptions())

    gx, gy = lp.grid_positions["Switch"]
    px, py = _iso_project(lp.layout, gx, gy)
    expected = (px + lp.offset_x, py + lp.offset_y)

    line = _iso_grid_line(lp.layout, (gx, gy), (gx, gy), "#eee", lp.offset_x, lp.offset_y)
    assert _line_start(line) == expected
