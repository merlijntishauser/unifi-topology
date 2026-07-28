"""Node faces must agree with the theme, and the floor grid must be optional."""

from __future__ import annotations

import dataclasses
import re

import pytest

from unifi_topology.model.topology import Edge
from unifi_topology.render._svg_iso_lighting import iso_face_colors
from unifi_topology.render._svg_iso_node_render import _ICON_TILE_RATIO
from unifi_topology.render.svg_isometric import render_svg_isometric
from unifi_topology.render.svg_theme import DEFAULT_THEME, SvgOptions, node_type_gradients

pytestmark = pytest.mark.unit

_EDGES = [Edge("sw", "ap", label="Switch: Port 1")]
_TYPES = {"sw": "switch", "ap": "ap"}


def _node_body(svg: str, node_id: str) -> str:
    match = re.search(rf'<g class="unm-node" data-node-id="{node_id}"(.*?)</g>', svg, re.S)
    assert match, f"node {node_id} not rendered"
    return match.group(1)


class TestFaceColoursFollowTheTheme:
    """A hardcoded palette here left the sides green under a theme whose APs are blue."""

    def test_faces_change_with_the_theme(self):
        blue = dataclasses.replace(DEFAULT_THEME, node_ap=("#6baeff", "#4797ff"))
        assert iso_face_colors("ap", DEFAULT_THEME) != iso_face_colors("ap", blue)

    def test_faces_are_shaded_from_the_top_face_colour(self):
        theme = dataclasses.replace(DEFAULT_THEME, node_ap=("#6baeff", "#4797ff"))
        left, right = iso_face_colors("ap", theme)
        top = dict(node_type_gradients(theme))["ap"][0]
        # Same hue family as the top, and progressively darker away from the light.
        for face in (left, right):
            assert int(face[1:3], 16) < int(top[1:3], 16)
            assert int(face[5:7], 16) < int(top[5:7], 16)
        assert int(right[1:3], 16) < int(left[1:3], 16)

    def test_an_unknown_node_type_falls_back_without_raising(self):
        assert iso_face_colors("not-a-type", DEFAULT_THEME) == iso_face_colors(
            "other", DEFAULT_THEME
        )

    def test_rendered_sides_match_the_rendered_top(self):
        theme = dataclasses.replace(DEFAULT_THEME, node_ap=("#6baeff", "#4797ff"), icon_set="unifi")
        svg = render_svg_isometric(
            _EDGES, node_types=_TYPES, options=SvgOptions(iso_lighting=True), theme=theme
        )
        body = _node_body(svg, "ap")
        assert 'fill="url(#iso-node-ap)"' in body
        sides = re.findall(r'class="label-tile-side"[^>]*fill="(#[0-9a-f]{6})"', body)
        assert sides == list(iso_face_colors("ap", theme))


class TestGridVisibility:
    def test_the_grid_is_drawn_by_default(self):
        svg = render_svg_isometric(_EDGES, node_types=_TYPES)
        assert 'class="iso-grid"' in svg

    def test_the_grid_can_be_hidden(self):
        svg = render_svg_isometric(
            _EDGES, node_types=_TYPES, options=SvgOptions(iso_show_grid=False)
        )
        assert 'class="iso-grid"' not in svg

    def test_hiding_the_grid_leaves_the_nodes_alone(self):
        with_grid = render_svg_isometric(_EDGES, node_types=_TYPES)
        without = render_svg_isometric(
            _EDGES, node_types=_TYPES, options=SvgOptions(iso_show_grid=False)
        )
        assert _node_body(with_grid, "ap") == _node_body(without, "ap")

    def test_the_canvas_is_unchanged_by_hiding_the_grid(self):
        pattern = r'viewBox="([^"]+)"'
        with_grid = re.search(pattern, render_svg_isometric(_EDGES, node_types=_TYPES))
        without = re.search(
            pattern,
            render_svg_isometric(
                _EDGES, node_types=_TYPES, options=SvgOptions(iso_show_grid=False)
            ),
        )
        assert with_grid and without and with_grid.group(1) == without.group(1)


def test_icons_do_not_overhang_their_tile_far():
    """Sized to sit on the tile; well above this and they float over its edges."""
    assert _ICON_TILE_RATIO <= 1.15
