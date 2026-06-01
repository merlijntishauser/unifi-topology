"""End-to-end checks that rendered SVG is well-formed XML.

A control character (e.g. U+0003) coming from a misencoded device or client
name must never leak into the output: such characters cannot appear in a
well-formed XML document at all, and a single one breaks the entire render for
downstream consumers (browser DOMParser, HA dashboard card, etc.).
"""

from __future__ import annotations

from defusedxml.minidom import parseString

import unifi_topology.render.svg as svg_module
import unifi_topology.render.svg_isometric as svg_iso_module
from unifi_topology.model.topology import Edge

# A name carrying a control character used directly as a node id, so it flows
# into both text-content (the label) and attribute (data-node-id / data-edge-*)
# contexts.
DIRTY_NAME = "My\x03Phone\x00"


def _assert_well_formed(svg: str) -> None:
    assert "\x03" not in svg
    assert "\x00" not in svg
    parseString(svg)  # raises if not well-formed


def test_orthogonal_render_is_well_formed_with_control_chars():
    svg = svg_module.render_svg(
        [Edge(DIRTY_NAME, "Switch")],
        node_types={DIRTY_NAME: "client", "Switch": "switch"},
    )
    _assert_well_formed(svg)


def test_isometric_render_is_well_formed_with_control_chars():
    svg = svg_iso_module.render_svg_isometric(
        [Edge(DIRTY_NAME, "Switch")],
        node_types={DIRTY_NAME: "client", "Switch": "switch"},
    )
    _assert_well_formed(svg)
