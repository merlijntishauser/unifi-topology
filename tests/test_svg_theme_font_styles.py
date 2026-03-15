import unifi_topology.render.svg_theme as svg_theme_module


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


def test_svg_style_block_iso_mode():
    block = svg_theme_module._svg_style_block(svg_theme_module.DEFAULT_THEME, 12, iso=True)
    assert "not(.group-label)" in block
