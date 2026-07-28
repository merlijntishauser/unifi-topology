"""Tests for the isometric light model, contact shadows, and data elevation."""

from __future__ import annotations

from unifi_topology.model.topology import Edge
from unifi_topology.render._svg_iso_lighting import _shade, iso_face_colors
from unifi_topology.render.svg_isometric import render_svg_isometric
from unifi_topology.render.svg_theme import DEFAULT_THEME, SvgOptions

_EDGES = [Edge("gw", "sw"), Edge("sw", "ap")]
_TYPES = {"gw": "gateway", "sw": "switch", "ap": "ap"}


def test_shade_scales_channels():
    assert _shade("#808080", 0.5) == "#404040"
    assert _shade("#ffffff", 2.0) == "#ffffff"  # clamped
    assert _shade("not-a-color", 0.5) == "not-a-color"


def test_face_colors_derive_from_node_type():
    left, right = iso_face_colors("switch", DEFAULT_THEME)
    # Both faces are shaded from the node's own colour, and the right face
    # (angled furthest from the light) is darker than the left.
    assert left != right
    assert left.startswith("#") and right.startswith("#")
    assert int(right[1:3], 16) < int(left[1:3], 16)


def test_lighting_is_opt_in():
    output = render_svg_isometric(_EDGES, node_types=_TYPES)
    assert 'class="iso-contact-shadow"' not in output


def test_lighting_adds_contact_shadows():
    output = render_svg_isometric(_EDGES, node_types=_TYPES, options=SvgOptions(iso_lighting=True))
    assert output.count('class="iso-contact-shadow"') == len(_TYPES)
