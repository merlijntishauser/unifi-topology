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


def test_isometric_icons_are_well_formed():
    for name in sorted(set(_ISO_ICON_FILES_ISOMETRIC.values())):
        markup = (_ISO_DIR / name).read_text()
        assert markup.rstrip().endswith("</svg>"), f"{name} is truncated"
        assert 'viewBox="' in markup, f"{name} has no viewBox"
        assert "<polygon" in markup or "<path" in markup, f"{name} has no geometry"


# isopacks covers none of these subjects, so they were once primitive stand-ins
# built from 7-10 flat polygons. They now come from the UniFi set, recoloured by
# scripts/recolour_icons.py; real artwork in this style runs to dozens of shapes.
_ONCE_PLACEHOLDERS = ("camera.svg", "speaker.svg", "gameconsole.svg", "sensor.svg")


def test_no_primitive_placeholders_remain():
    thin = {
        name: count
        for name in _ONCE_PLACEHOLDERS
        if (count := (_ISO_DIR / name).read_text().count("<polygon")) < 20
    }
    assert thin == {}, f"primitive stand-ins are back: {thin}"


def test_recoloured_icons_use_the_isopacks_palette():
    """A grey from the UniFi palette here would read as a foreign library."""
    for name in _ONCE_PLACEHOLDERS:
        markup = (_ISO_DIR / name).read_text().upper()
        for grey in ("#24282B", "#798187", "#A0AAB4", "#CBD3DA", "#4A535C"):
            assert grey not in markup, f"{name} still carries UniFi grey {grey}"
        assert "#231F20" in markup, f"{name} is missing the isopacks outline colour"


def test_notice_records_the_non_isopacks_files():
    notice = (_ISO_DIR / "NOTICE").read_text()
    for name in _ONCE_PLACEHOLDERS:
        assert name in notice, f"{name} is not declared in the isometric NOTICE"
