from dataclasses import replace
from pathlib import Path

import unifi_topology.render.svg as svg_module
import unifi_topology.render.svg_icons as svg_icons_module
import unifi_topology.render.svg_isometric as svg_iso_module
import unifi_topology.render.svg_theme as svg_theme_module
from unifi_topology.model.topology import Edge


def test_load_icons_missing_files_returns_empty(monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda _self: False)
    assert svg_module._load_icons() == {}


def test_load_isometric_icons_missing_files_returns_empty(monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda _self: False)
    assert svg_icons_module._load_isometric_icons() == {}


def test_load_isometric_icons_isometric():
    icons = svg_icons_module._load_isometric_icons("isometric")
    assert "gateway" in icons
    assert "switch" in icons
    assert "ap" in icons
    assert "client" in icons
    assert "other" in icons
    assert all(value.startswith("data:image/svg+xml;base64,") for value in icons.values())


def test_load_isometric_icons_modern():
    icons = svg_icons_module._load_isometric_icons("modern")
    assert "gateway" in icons
    assert "switch" in icons
    assert "ap" in icons
    assert "client" in icons
    assert "other" in icons
    assert all(value.startswith("data:image/svg+xml;base64,") for value in icons.values())


def test_load_isometric_icons_fallback_to_isometric():
    icons = svg_icons_module._load_isometric_icons("nonexistent_set")
    assert "gateway" in icons
    assert icons


def test_load_icons_isometric():
    icons = svg_module._load_icons("isometric")
    assert "gateway" in icons
    assert "switch" in icons


def test_load_icons_modern():
    icons = svg_module._load_icons("modern")
    assert "gateway" in icons
    assert "switch" in icons


def test_darken_hex_basic():
    assert svg_icons_module._darken_hex("#ffffff", 0.5) == "#7f7f7f"
    assert svg_icons_module._darken_hex("#000000", 0.5) == "#000000"


def test_darken_hex_typical_factor():
    assert svg_icons_module._darken_hex("#006fff", 0.35) == "#0048a5"


def test_darken_hex_zero_factor():
    assert svg_icons_module._darken_hex("#ff8000", 0.0) == "#ff8000"


def test_darken_hex_invalid_input():
    assert svg_icons_module._darken_hex("not-a-color", 0.35) == "not-a-color"
    assert svg_icons_module._darken_hex("#fff", 0.35) == "#fff"


def test_build_decal_colors_returns_all_node_types():
    colors = svg_icons_module._build_decal_colors(svg_theme_module.DEFAULT_THEME)
    expected = {
        "gateway",
        "switch",
        "ap",
        "client",
        "other",
        "client_cluster",
        "camera",
        "tv",
        "phone",
        "printer",
        "nas",
        "speaker",
        "game_console",
        "iot",
    }
    assert set(colors.keys()) == expected
    for color in colors.values():
        assert color.startswith("#")
        assert len(color) == 7


def test_build_decal_colors_are_darker_than_source():
    colors = svg_icons_module._build_decal_colors(svg_theme_module.DEFAULT_THEME)
    source = svg_theme_module.DEFAULT_THEME.node_gateway[1]
    decal = colors["gateway"]
    src_sum = sum(int(source[i : i + 2], 16) for i in (1, 3, 5))
    dec_sum = sum(int(decal[i : i + 2], 16) for i in (1, 3, 5))
    assert dec_sum < src_sum


def test_build_font_style_none():
    face, family = svg_theme_module._build_font_style(None)
    assert face == ""
    assert family == "Arial,Helvetica,sans-serif"


def test_build_font_style_unknown_font():
    face, family = svg_theme_module._build_font_style("Nonexistent Font")
    assert face == ""
    assert family == "Arial,Helvetica,sans-serif"


def test_build_font_style_inter():
    face, family = svg_theme_module._build_font_style("Inter")
    assert "@font-face" in face
    assert "font-weight:400" in face
    assert "font-weight:600" in face
    assert "'Inter'" in family


def test_build_font_style_space_grotesk():
    face, family = svg_theme_module._build_font_style("Space Grotesk")
    assert "@font-face" in face
    assert "'Space Grotesk'" in family


def test_svg_style_block_no_font():
    block = svg_theme_module._svg_style_block(svg_theme_module.DEFAULT_THEME, 12)
    assert "<style>" in block
    assert "font-weight:600" in block
    assert "@font-face" not in block


def test_svg_style_block_with_font():
    block = svg_theme_module._svg_style_block(
        replace(svg_theme_module.DEFAULT_THEME, font_family="Inter"),
        12,
    )
    assert "@font-face" in block
    assert "'Inter'" in block
    assert "node-label" in block


def test_svg_style_block_iso_mode():
    block = svg_theme_module._svg_style_block(svg_theme_module.DEFAULT_THEME, 12, iso=True)
    assert "not(.group-label)" in block


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


def test_load_icons_primary_missing_falls_back_to_isometric(monkeypatch):
    patched_sets = {
        "custom": (
            "nonexistent-dir",
            "isometric",
            svg_icons_module._ICON_FILES_ISOMETRIC,
            svg_icons_module._ISO_ICON_FILES_ISOMETRIC,
        ),
        "isometric": svg_icons_module._ICON_SETS["isometric"],
    }
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    icons = svg_icons_module._load_icons("custom")
    assert "gateway" in icons
    assert icons["gateway"].startswith("data:image/svg+xml;base64,")


def test_load_icons_no_filename_in_primary_falls_back(monkeypatch):
    patched_sets = {
        "sparse": (
            "",
            "isometric",
            {},
            svg_icons_module._ISO_ICON_FILES_ISOMETRIC,
        ),
        "isometric": svg_icons_module._ICON_SETS["isometric"],
    }
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    icons = svg_icons_module._load_icons("sparse")
    assert "gateway" in icons
    assert "switch" in icons


def test_load_icons_no_fallback_filename_skips(monkeypatch):
    patched_sets = {
        "isometric": (
            "",
            "isometric",
            {},
            svg_icons_module._ISO_ICON_FILES_ISOMETRIC,
        ),
    }
    patched_sets["isometric"] = ("", "isometric", {}, svg_icons_module._ISO_ICON_FILES_ISOMETRIC)
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    assert len(svg_icons_module._load_icons("isometric")) == 0


def test_load_isometric_icons_primary_missing_falls_back(monkeypatch):
    patched_sets = {
        "custom": (
            "",
            "nonexistent-iso-dir",
            svg_icons_module._ICON_FILES_ISOMETRIC,
            svg_icons_module._ISO_ICON_FILES_ISOMETRIC,
        ),
        "isometric": svg_icons_module._ICON_SETS["isometric"],
    }
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    icons = svg_icons_module._load_isometric_icons("custom")
    assert "gateway" in icons
    assert icons["gateway"].startswith("data:image/svg+xml;base64,")


def test_load_isometric_icons_no_filename_in_primary_falls_back(monkeypatch):
    patched_sets = {
        "sparse": (
            "",
            "isometric",
            svg_icons_module._ICON_FILES_ISOMETRIC,
            {},
        ),
        "isometric": svg_icons_module._ICON_SETS["isometric"],
    }
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    icons = svg_icons_module._load_isometric_icons("sparse")
    assert "gateway" in icons
    assert "switch" in icons


def test_load_isometric_icons_no_fallback_filename_skips(monkeypatch):
    patched_sets = {
        "isometric": (
            "",
            "isometric",
            svg_icons_module._ICON_FILES_ISOMETRIC,
            {},
        ),
    }
    patched_sets["isometric"] = (
        "",
        "isometric",
        svg_icons_module._ICON_FILES_ISOMETRIC,
        {},
    )
    monkeypatch.setattr(svg_icons_module, "_ICON_SETS", patched_sets)
    assert len(svg_icons_module._load_isometric_icons("isometric")) == 0
