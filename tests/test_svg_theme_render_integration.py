from dataclasses import replace

import unifi_topology.render.svg as svg_module
import unifi_topology.render.svg_isometric as svg_iso_module
import unifi_topology.render.svg_theme as svg_theme_module
from unifi_topology.model.topology import Edge


def test_render_svg_uses_theme_icon_set():
    output = svg_module.render_svg(
        [Edge("A", "B")],
        node_types={"A": "gateway", "B": "switch"},
        theme=replace(svg_theme_module.DEFAULT_THEME, icon_set="modern"),
    )
    assert "<svg" in output


def test_render_svg_isometric_uses_theme_icon_set():
    output = svg_iso_module.render_svg_isometric(
        [Edge("A", "B")],
        node_types={"A": "gateway", "B": "switch"},
        theme=replace(svg_theme_module.DEFAULT_THEME, icon_set="modern"),
    )
    assert "<svg" in output


def test_node_outline_follows_restyled_theme_fill():
    from unifi_topology.render.svg_theme import DEFAULT_THEME
    from unifi_topology.render.theme import resolve_svg_themes

    unifi = resolve_svg_themes("unifi")
    assert DEFAULT_THEME.node_outline("gateway") == "#f08a00"
    assert unifi.node_outline("gateway") == "#0048a5"
    assert resolve_svg_themes("blueprint").node_outline("gateway") == "#eaf2ff"


def test_darken_hex_passes_through_named_colours():
    from unifi_topology.render.svg_theme import _darken_hex

    assert _darken_hex("orange") == "orange"
