"""Icons must sit on their tile, not hover above it.

The access point lift was tuned for the isopacks radio mast, whose artwork sits
high in its own frame. Applied to the UniFi set -- normalized to a common frame
by scripts/normalize_icon_viewbox.py -- it left the flat ceiling disc floating a
whole tile height above the node.
"""

from __future__ import annotations

import pytest

from unifi_topology.render._svg_iso_node_render import _ICON_SET_EXTRA_LIFT, _icon_y_offset

pytestmark = pytest.mark.unit

TILE_H = 100.0


def _lift(node_type: str, icon_set: str, *, port_label: str | None = None) -> float:
    return _icon_y_offset(
        node_type=node_type,
        is_client=False,
        port_label=port_label,
        tile_h=TILE_H,
        icon_set=icon_set,
    )


def test_isopacks_access_point_keeps_its_lift():
    """Legacy output must not shift; the mast still needs raising."""
    assert _lift("ap", "isometric") - _lift("switch", "isometric") == pytest.approx(40.0)


def test_unifi_access_point_is_not_lifted_above_its_tile():
    assert _lift("ap", "unifi") == _lift("switch", "unifi")


def test_unknown_icon_set_gets_no_extra_lift():
    assert _lift("ap", "somethingelse") == _lift("switch", "somethingelse")


def test_base_seating_offset_is_shared_by_all_sets():
    """Only the per-set extra differs; the base offset is common."""
    assert _lift("switch", "isometric") == _lift("switch", "unifi")


@pytest.mark.parametrize("icon_set", sorted(_ICON_SET_EXTRA_LIFT))
def test_configured_lifts_only_target_known_node_types(icon_set: str):
    from unifi_topology.render.svg_icons import _ICON_FILES_ISOMETRIC

    unknown = set(_ICON_SET_EXTRA_LIFT[icon_set]) - set(_ICON_FILES_ISOMETRIC)
    assert unknown == set(), f"{icon_set} lifts unknown node types: {unknown}"


def test_port_label_reduces_the_base_offset():
    """A node with a port label already sits on a pedestal."""
    assert _lift("switch", "unifi", port_label="Port 1") < _lift("switch", "unifi")
