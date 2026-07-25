"""Every node type must map to its own existing isometric icon."""

from __future__ import annotations

import pathlib

from unifi_topology.render.svg_icons import (
    _ICON_FILES_ISOMETRIC,
    _ICON_FILES_MODERN,
    _ISO_ICON_FILES_ISOMETRIC,
    _icon_base_path,
)

_ISO_DIR = pathlib.Path(_icon_base_path()) / "isometric"


def test_every_node_type_has_a_distinct_isometric_icon():
    """Guards the regression where 8 of 14 types all rendered as a laptop."""
    files = list(_ISO_ICON_FILES_ISOMETRIC.values())
    assert len(set(files)) == len(files), "two node types share an isometric icon"


def test_isometric_icon_files_all_exist():
    missing = sorted(
        f for f in set(_ISO_ICON_FILES_ISOMETRIC.values()) if not (_ISO_DIR / f).exists()
    )
    assert missing == []


def test_node_type_keys_match_across_icon_sets():
    assert set(_ISO_ICON_FILES_ISOMETRIC) == set(_ICON_FILES_ISOMETRIC)
    assert set(_ISO_ICON_FILES_ISOMETRIC) == set(_ICON_FILES_MODERN)


def test_generated_icons_are_well_formed():
    # printer.svg comes from upstream isopacks; these four are generated placeholders.
    for name in ("camera.svg", "speaker.svg", "gameconsole.svg", "sensor.svg"):
        markup = (_ISO_DIR / name).read_text()
        assert markup.startswith("<svg"), f"{name} is not an svg root"
        assert markup.rstrip().endswith("</svg>"), f"{name} is truncated"
        assert 'viewBox="' in markup, f"{name} has no viewBox"
        assert markup.count("<polygon") >= 3, f"{name} has no isometric faces"
