import pytest

from unifi_topology.render.theme import (
    BUILTIN_THEMES,
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
