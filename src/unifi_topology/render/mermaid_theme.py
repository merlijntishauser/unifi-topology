"""Mermaid theming helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MermaidTheme:
    node_gateway: tuple[str, str]
    node_switch: tuple[str, str]
    node_ap: tuple[str, str]
    node_client: tuple[str, str]
    node_other: tuple[str, str]
    poe_link: str
    poe_link_width: int
    poe_link_arrow: str
    standard_link: str
    standard_link_width: int
    standard_link_arrow: str
    node_wan: tuple[str, str] = ("#e0f0ff", "#0288d1")
    node_text: str | None = None
    edge_label_border: str | None = None
    edge_label_border_width: int | None = None


DEFAULT_THEME = MermaidTheme(
    node_gateway=("#ffe3b3", "#d98300"),
    node_switch=("#d6ecff", "#3a7bd5"),
    node_ap=("#d7f5e7", "#27ae60"),
    node_client=("#f2e5ff", "#7f3fbf"),
    node_other=("#eeeeee", "#8f8f8f"),
    node_wan=("#e0f0ff", "#0288d1"),
    poe_link="#1e88e5",
    poe_link_width=2,
    poe_link_arrow="none",
    standard_link="#2ecc71",
    standard_link_width=2,
    standard_link_arrow="none",
    node_text=None,
    edge_label_border=None,
    edge_label_border_width=None,
)


def _node_class_def(name: str, fill: str, stroke: str, text_color: str | None) -> str:
    color = f",color:{text_color}" if text_color else ""
    return f"  classDef {name} fill:{fill},stroke:{stroke},stroke-width:1px{color};"


def class_defs(theme: MermaidTheme = DEFAULT_THEME) -> list[str]:
    pairs = [
        ("node_gateway", theme.node_gateway),
        ("node_switch", theme.node_switch),
        ("node_ap", theme.node_ap),
        ("node_client", theme.node_client),
        ("node_other", theme.node_other),
        ("node_wan", theme.node_wan),
    ]
    lines = [_node_class_def(name, fill, stroke, theme.node_text) for name, (fill, stroke) in pairs]
    lines.append("  classDef node_legend font-size:10px;")
    return lines
