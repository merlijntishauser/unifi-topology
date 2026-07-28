"""The blueprint theme and the two theme overrides it introduced.

Blueprint is monochrome: one white line colour for every outline, and flat
white icon decals. Neither was expressible before -- node strokes came from the
hardcoded orthogonal palette, and isometric decals were always derived by
darkening each node's gradient, which vanishes on dark fills.
"""

from __future__ import annotations

import base64
import re

import pytest

from unifi_topology import render_svg, render_svg_isometric, resolve_svg_themes
from unifi_topology.model.topology import Edge
from unifi_topology.render.svg_theme import DEFAULT_THEME, SvgOptions

pytestmark = pytest.mark.unit

_EDGES = [Edge("gw", "sw"), Edge("sw", "ap", label="Switch: Port 1")]
_TYPES = {"gw": "gateway", "sw": "switch", "ap": "ap"}
_LINE = "#eaf2ff"


@pytest.fixture(scope="module")
def blueprint():
    return resolve_svg_themes(theme_name="blueprint")


def test_blueprint_is_a_builtin(blueprint):
    assert blueprint.background == "#1a3a67"
    assert blueprint.node_stroke == _LINE
    assert blueprint.icon_decal_iso == _LINE
    assert blueprint.icon_set == "modern"


def test_every_node_outline_is_the_line_colour_isometric(blueprint):
    svg = render_svg_isometric(_EDGES, node_types=_TYPES, theme=blueprint)
    strokes = set()
    for match in re.finditer(r'<g class="unm-node".*?</g>', svg, re.S):
        strokes.update(re.findall(r'stroke="(#[0-9a-fA-F]{6})"', match.group(0)))
    assert strokes == {_LINE}


def test_every_node_outline_is_the_line_colour_orthogonal(blueprint):
    svg = render_svg(_EDGES, node_types=_TYPES, theme=blueprint)
    strokes = re.findall(r'<rect[^>]*fill="url\(#node-[a-z_]+\)"[^>]*stroke="([^"]+)"', svg)
    assert strokes and set(strokes) == {_LINE}


def test_isometric_decals_are_flat_white(blueprint):
    svg = render_svg_isometric(_EDGES, node_types=_TYPES, theme=blueprint)
    payloads = {
        base64.b64decode(uri).decode()
        for uri in re.findall(r'href="data:image/svg\+xml;base64,([^"]+)"', svg)
    }
    assert payloads, "no icons rendered"
    for markup in payloads:
        assert _LINE.upper() in markup.upper()
        assert "#DECAL0" not in markup


def test_default_theme_keeps_per_type_strokes():
    """The overrides must be inert when a theme does not set them."""
    assert DEFAULT_THEME.node_stroke is None
    assert DEFAULT_THEME.icon_decal_iso is None
    svg = render_svg_isometric(_EDGES, node_types=_TYPES)
    match = re.search(r'<g class="unm-node" data-node-id="gw".*?</g>', svg, re.S)
    assert match, "gateway node not rendered"
    assert 'stroke="#f08a00"' in match.group(0)  # gateway's palette stroke, as before


def test_blueprint_renders_with_every_option_on(blueprint):
    svg = render_svg_isometric(
        _EDGES,
        node_types=_TYPES,
        options=SvgOptions(iso_lighting=True, iso_compact_layout=True, iso_route_around_nodes=True),
        theme=blueprint,
    )
    assert 'class="iso-grid"' in svg
    assert svg.count("unm-node") >= len(_TYPES)
