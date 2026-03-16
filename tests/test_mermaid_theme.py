"""Tests for MermaidTheme dataclass and class_defs."""

from unifi_topology.render.mermaid_theme import DEFAULT_THEME, MermaidTheme, class_defs


def test_default_theme_is_frozen():
    assert isinstance(DEFAULT_THEME, MermaidTheme)
    assert DEFAULT_THEME.poe_link == "#1e88e5"
    assert DEFAULT_THEME.standard_link == "#2ecc71"


def test_class_defs_returns_all_node_types():
    defs = class_defs()
    text = "\n".join(defs)
    assert "node_gateway" in text
    assert "node_switch" in text
    assert "node_ap" in text
    assert "node_client" in text
    assert "node_other" in text
    assert "node_wan" in text
    assert "node_legend" in text


def test_class_defs_includes_text_color():
    theme = MermaidTheme(
        node_gateway=("#fff", "#000"),
        node_switch=("#fff", "#000"),
        node_ap=("#fff", "#000"),
        node_client=("#fff", "#000"),
        node_other=("#fff", "#000"),
        poe_link="#blue",
        poe_link_width=2,
        poe_link_arrow="none",
        standard_link="#green",
        standard_link_width=2,
        standard_link_arrow="none",
        node_text="#333",
    )
    defs = class_defs(theme)
    text = "\n".join(defs)
    assert "color:#333" in text


def test_default_theme_has_no_text_color():
    defs = class_defs(DEFAULT_THEME)
    text = "\n".join(defs)
    assert "color:" not in text
