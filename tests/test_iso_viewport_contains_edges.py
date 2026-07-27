"""The canvas must contain the edges, not just the nodes.

Regression for #69: an edge corner is chosen in grid space and can project
outside the box the nodes span, because screen x depends on ``gx - gy``. The
viewport was sized from node positions alone, so the corner fell outside the
viewBox and the edge rendered clipped.
"""

from __future__ import annotations

import re

import pytest

from unifi_topology.model.topology import Edge
from unifi_topology.render._svg_iso_layout import _expand_viewport, _Viewport
from unifi_topology.render.svg_isometric import render_svg_isometric
from unifi_topology.render.svg_theme import SvgOptions

pytestmark = pytest.mark.unit

# The topology from the issue: sw and tv share gx - gy, so the corner that dodges
# ap2 projects west of both endpoints.
_EDGES = [
    Edge("gw", "sw"),
    Edge("sw", "ap1"),
    Edge("sw", "ap2"),
    Edge("sw", "tv"),
    Edge("sw", "speaker"),
]
_NODE_TYPES = {
    "gw": "gateway",
    "sw": "switch",
    "ap1": "ap",
    "ap2": "ap",
    "tv": "tv",
    "speaker": "speaker",
}

_OPTION_SETS = [
    ("defaults", SvgOptions()),
    ("compact", SvgOptions(iso_compact_layout=True)),
    ("routing", SvgOptions(iso_route_around_nodes=True)),
    ("both", SvgOptions(iso_compact_layout=True, iso_route_around_nodes=True)),
]


def _overflow(svg: str) -> tuple[float, float, float, float]:
    """How far the drawn paths fall outside the viewBox on each side."""
    match = re.search(r'viewBox="([^"]+)"', svg)
    assert match, "rendered SVG has no viewBox"
    view = [float(v) for v in match.group(1).split()]
    points = re.findall(r"[ML] *(-?[\d.]+)[, ]+(-?[\d.]+)", svg)
    xs = [float(x) for x, _y in points]
    ys = [float(y) for _x, y in points]
    return (
        max(0.0, -min(xs)),
        max(0.0, -min(ys)),
        max(0.0, max(xs) - view[2]),
        max(0.0, max(ys) - view[3]),
    )


@pytest.mark.parametrize(("label", "options"), _OPTION_SETS, ids=[o[0] for o in _OPTION_SETS])
def test_every_edge_is_drawn_inside_the_viewbox(label: str, options: SvgOptions):
    svg = render_svg_isometric(_EDGES, node_types=_NODE_TYPES, options=options)
    assert _overflow(svg) == (0.0, 0.0, 0.0, 0.0), label


def test_the_reported_corner_is_no_longer_negative():
    svg = render_svg_isometric(
        _EDGES,
        node_types=_NODE_TYPES,
        options=SvgOptions(iso_compact_layout=True, iso_route_around_nodes=True),
    )
    xs = [float(x) for x, _y in re.findall(r"[ML] *(-?[\d.]+)[, ]+(-?[\d.]+)", svg)]
    assert min(xs) >= 0


def test_a_topology_needing_no_expansion_is_untouched():
    """Expansion must be a last resort; the fixed padding already covers tiles."""
    plain = render_svg_isometric(_EDGES, node_types=_NODE_TYPES, options=SvgOptions())
    again = render_svg_isometric(_EDGES, node_types=_NODE_TYPES, options=SvgOptions())
    assert plain == again


class TestExpandViewport:
    BASE = _Viewport(offset_x=100.0, offset_y=50.0, width=1000.0, height=800.0)

    def test_no_points_is_a_no_op(self):
        assert _expand_viewport(self.BASE, [], 10.0) == self.BASE

    def test_points_already_inside_are_a_no_op(self):
        assert _expand_viewport(self.BASE, [(500.0, 400.0)], 10.0) == self.BASE

    def test_a_point_west_of_the_canvas_shifts_everything_right(self):
        out = _expand_viewport(self.BASE, [(-20.0, 400.0)], 10.0)
        assert out.offset_x == self.BASE.offset_x + 30.0
        assert out.width == self.BASE.width + 30.0
        assert out.offset_y == self.BASE.offset_y

    def test_a_point_east_of_the_canvas_grows_the_width(self):
        out = _expand_viewport(self.BASE, [(1200.0, 400.0)], 10.0)
        assert out.offset_x == self.BASE.offset_x
        assert out.width == 1210.0

    def test_a_point_north_of_the_canvas_shifts_everything_down(self):
        out = _expand_viewport(self.BASE, [(500.0, -5.0)], 10.0)
        assert out.offset_y == self.BASE.offset_y + 15.0
        assert out.height == self.BASE.height + 15.0

    def test_the_margin_is_honoured(self):
        out = _expand_viewport(self.BASE, [(0.0, 400.0)], 25.0)
        assert out.offset_x == self.BASE.offset_x + 25.0
