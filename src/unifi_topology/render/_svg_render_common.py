"""Private helpers shared by orthogonal and isometric SVG renderers."""

from __future__ import annotations

from collections.abc import Callable

from .svg_theme import SvgOptions, SvgTheme, _svg_style_block, svg_defs


def start_svg_document(
    *,
    width: float,
    height: float,
    out_width: float | int,
    out_height: float | int,
    theme: SvgTheme,
    options: SvgOptions,
    defs_prefix: str = "",
    iso: bool = False,
) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{out_width}" height="{out_height}" '
        f'viewBox="0 0 {width} {height}">',
        svg_defs(defs_prefix, theme),
        _svg_style_block(theme, options.font_size, iso=iso),
        f'<rect width="100%" height="100%" fill="{theme.background}"/>',
    ]


def finish_svg_document(lines: list[str]) -> str:
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _find_gateway_position(
    node_types: dict[str, str],
    positions: dict[str, tuple[float, float]],
) -> tuple[float, float] | None:
    """Find the position of the gateway node."""
    for name, node_type in node_types.items():
        if node_type == "gateway" and name in positions:
            return positions[name]
    return None


def _overlay_box_size(
    icon_size: float,
    padding: float,
    font_size: int,
    label_lines: list[str],
) -> tuple[float, float]:
    """Compute (width, height) for a WAN/VPN overlay box from its label content.

    Shared by the orthogonal and isometric WAN and VPN overlays, which all use
    the same icon + text-column sizing formula.
    """
    line_height = font_size + 4
    max_text_width = max((len(line) for line in label_lines), default=10) * font_size * 0.55
    box_width = max(icon_size + padding * 2, max_text_width + padding * 2)
    box_height = icon_size + len(label_lines) * line_height + padding * 3
    return box_width, box_height


def render_at_gateway[TPosition, TContent](
    *,
    lines: list[str],
    content: TContent | None,
    node_types: dict[str, str],
    positions: dict[str, TPosition],
    find_gateway_position: Callable[[dict[str, str], dict[str, TPosition]], TPosition | None],
    render: Callable[[list[str], TContent, TPosition], None],
) -> None:
    if not content:
        return
    gateway_pos = find_gateway_position(node_types, positions)
    if gateway_pos is not None:
        render(lines, content, gateway_pos)
