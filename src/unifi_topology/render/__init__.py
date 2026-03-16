"""SVG rendering backends for network diagrams."""

from .inventory import render_device_inventory_table
from .lldp import render_lldp_md
from .markdown import render_device_port_overview
from .mermaid import render_legend, render_legend_compact, render_mermaid
from .mermaid_theme import DEFAULT_THEME as DEFAULT_MERMAID_THEME
from .mermaid_theme import MermaidTheme
from .svg import render_dual, render_svg
from .svg_isometric import render_svg_isometric
from .svg_theme import DEFAULT_THEME as DEFAULT_SVG_THEME
from .svg_theme import SvgOptions, SvgTheme
from .theme import resolve_svg_themes

__all__ = [
    "DEFAULT_MERMAID_THEME",
    "DEFAULT_SVG_THEME",
    "MermaidTheme",
    "SvgOptions",
    "SvgTheme",
    "render_device_inventory_table",
    "render_device_port_overview",
    "render_dual",
    "render_legend",
    "render_legend_compact",
    "render_lldp_md",
    "render_mermaid",
    "render_svg",
    "render_svg_isometric",
    "resolve_svg_themes",
]
