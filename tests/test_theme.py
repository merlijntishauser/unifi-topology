import pytest

from unifi_topology.render.theme import (
    BUILTIN_THEMES,
    _coerce_pair,
    _coerce_vlan_colors,
    builtin_theme_yaml_path,
    load_svg_theme,
    resolve_svg_themes,
)


def test_load_svg_theme_rejects_non_object(tmp_path):
    path = tmp_path / "theme.yaml"
    path.write_text("- nope\n", encoding="utf-8")

    try:
        load_svg_theme(path)
    except ValueError as exc:
        message = str(exc)
    else:
        message = ""

    assert "Theme file must contain a YAML mapping" in message


def test_load_svg_theme_applies_link_colors(tmp_path):
    path = tmp_path / "theme.yaml"
    path.write_text(
        'svg:\n  links:\n    standard:\n      from: "#abc"\n      to: "#def"\n',
        encoding="utf-8",
    )

    svg_theme = load_svg_theme(path)

    assert svg_theme.link_standard == ("#abc", "#def")


def test_load_svg_theme_applies_new_properties(tmp_path):
    """Test that theme properties (background, text, status, wan_globe) are loaded."""
    path = tmp_path / "theme.yaml"
    path.write_text(
        """svg:
  background: "#111"
  text:
    primary: "#222"
    secondary: "#333"
  status:
    online: "#444"
    offline: "#555"
  wan_globe:
    from: "#666"
    to: "#777"
""",
        encoding="utf-8",
    )

    svg_theme = load_svg_theme(path)

    assert svg_theme.background == "#111"
    assert svg_theme.text_primary == "#222"
    assert svg_theme.text_secondary == "#333"
    assert svg_theme.status_online == "#444"
    assert svg_theme.status_offline == "#555"
    assert svg_theme.wan_globe == ("#666", "#777")


def test_resolve_svg_themes_builtin_unifi():
    """Test that built-in unifi theme loads correctly."""
    svg_theme = resolve_svg_themes(theme_name="unifi")

    assert svg_theme.background == "#f9fafa"


def test_resolve_svg_themes_builtin_unifi_dark():
    """Test that built-in unifi-dark theme loads correctly."""
    svg_theme = resolve_svg_themes(theme_name="unifi-dark")

    assert svg_theme.background == "#1c1e21"
    assert svg_theme.text_primary == "#f9fafa"


def test_resolve_svg_themes_builtin_minimal():
    """Test that built-in minimal theme loads correctly."""
    svg_theme = resolve_svg_themes(theme_name="minimal")

    assert svg_theme.background == "#fafafa"


def test_resolve_svg_themes_builtin_classic():
    """Test that classic theme maps to default.yaml."""
    svg_theme = resolve_svg_themes(theme_name="classic")

    assert svg_theme.link_standard is not None


def test_resolve_svg_themes_file_takes_priority(tmp_path):
    """Test that theme_file takes priority over theme_name."""
    path = tmp_path / "custom.yaml"
    path.write_text(
        'svg:\n  background: "#custom"\n',
        encoding="utf-8",
    )

    svg_theme = resolve_svg_themes(
        theme_name="unifi",  # This should be ignored
        theme_file=path,
    )

    assert svg_theme.background == "#custom"


def test_resolve_svg_themes_invalid_name_raises():
    """Test that invalid theme name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown theme"):
        resolve_svg_themes(theme_name="invalid-theme")


def test_builtin_themes_all_exist():
    """Test that all built-in themes can be loaded."""
    for theme_name in BUILTIN_THEMES:
        svg_theme = resolve_svg_themes(theme_name=theme_name)
        assert svg_theme is not None


def test_coerce_pair_from_list():
    """Test _coerce_pair accepts a list of two strings."""
    result = _coerce_pair(["#aaa", "#bbb"], ("#000", "#111"))
    assert result == ("#aaa", "#bbb")


def test_coerce_pair_from_tuple():
    """Test _coerce_pair accepts a tuple of two strings."""
    result = _coerce_pair(("#ccc", "#ddd"), ("#000", "#111"))
    assert result == ("#ccc", "#ddd")


def test_coerce_pair_dict_non_string_values_returns_default():
    """Test _coerce_pair returns default when dict values are not strings."""
    result = _coerce_pair({"from": 123, "to": 456}, ("#000", "#111"))
    assert result == ("#000", "#111")


def test_coerce_vlan_colors_string_digit_keys():
    """Test _coerce_vlan_colors parses string-digit keys as integers."""
    result = _coerce_vlan_colors({"10": "#aaa", "20": "#bbb"})
    assert result == {10: "#aaa", 20: "#bbb"}


def test_coerce_vlan_colors_skips_non_string_color():
    """Test _coerce_vlan_colors skips entries where color is not a string."""
    result = _coerce_vlan_colors({1: 12345, 2: "#bbb"})
    assert result == {2: "#bbb"}


def test_builtin_theme_yaml_path_valid():
    """Test builtin_theme_yaml_path returns a path for a valid theme."""
    path = builtin_theme_yaml_path("unifi")
    assert path.exists()
    assert path.name == "unifi.yaml"


def test_builtin_theme_yaml_path_invalid_raises():
    """Test builtin_theme_yaml_path raises ValueError for unknown theme."""
    with pytest.raises(ValueError, match="Unknown theme"):
        builtin_theme_yaml_path("nonexistent-theme")


def test_resolve_svg_themes_no_args_returns_default():
    """Test resolve_svg_themes with no arguments returns the default theme."""
    from unifi_topology.render.svg_theme import DEFAULT_THEME

    result = resolve_svg_themes()
    assert result is DEFAULT_THEME
