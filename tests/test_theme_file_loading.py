from unifi_topology.render.theme import load_svg_theme


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
