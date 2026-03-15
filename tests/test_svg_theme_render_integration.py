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
