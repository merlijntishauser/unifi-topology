from dataclasses import replace

import unifi_topology.render.svg_icons as svg_icons_module
import unifi_topology.render.svg_theme as svg_theme_module


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


def test_svg_style_block_with_font():
    block = svg_theme_module._svg_style_block(
        replace(svg_theme_module.DEFAULT_THEME, font_family="Inter"),
        12,
    )
    assert "@font-face" in block
    assert "'Inter'" in block
    assert "node-label" in block
