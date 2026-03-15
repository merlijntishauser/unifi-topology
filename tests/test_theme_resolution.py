import pytest

from unifi_topology.render.theme import (
    BUILTIN_THEMES,
    builtin_theme_yaml_path,
    resolve_svg_themes,
)


def test_resolve_svg_themes_builtin_unifi():
    svg_theme = resolve_svg_themes(theme_name="unifi")
    assert svg_theme.background == "#f9fafa"


def test_resolve_svg_themes_builtin_unifi_dark():
    svg_theme = resolve_svg_themes(theme_name="unifi-dark")
    assert svg_theme.background == "#1c1e21"
    assert svg_theme.text_primary == "#f9fafa"


def test_resolve_svg_themes_builtin_minimal():
    svg_theme = resolve_svg_themes(theme_name="minimal")
    assert svg_theme.background == "#fafafa"


def test_resolve_svg_themes_builtin_classic():
    svg_theme = resolve_svg_themes(theme_name="classic")
    assert svg_theme.link_standard is not None


def test_resolve_svg_themes_file_takes_priority(tmp_path):
    path = tmp_path / "custom.yaml"
    path.write_text(
        'svg:\n  background: "#custom"\n',
        encoding="utf-8",
    )

    svg_theme = resolve_svg_themes(
        theme_name="unifi",
        theme_file=path,
    )

    assert svg_theme.background == "#custom"


def test_resolve_svg_themes_invalid_name_raises():
    with pytest.raises(ValueError, match="Unknown theme"):
        resolve_svg_themes(theme_name="invalid-theme")


def test_builtin_themes_all_exist():
    for theme_name in BUILTIN_THEMES:
        svg_theme = resolve_svg_themes(theme_name=theme_name)
        assert svg_theme is not None


def test_builtin_theme_yaml_path_valid():
    path = builtin_theme_yaml_path("unifi")
    assert path.exists()
    assert path.name == "unifi.yaml"


def test_builtin_theme_yaml_path_invalid_raises():
    with pytest.raises(ValueError, match="Unknown theme"):
        builtin_theme_yaml_path("nonexistent-theme")


def test_resolve_svg_themes_no_args_returns_default():
    from unifi_topology.render.svg_theme import DEFAULT_THEME

    result = resolve_svg_themes()
    assert result is DEFAULT_THEME
