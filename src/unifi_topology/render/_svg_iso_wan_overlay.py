"""Private helpers for isometric WAN and gateway overlays."""

from __future__ import annotations

from ..model.topology import VpnTunnel, WanInfo
from .svg_iso_geometry import IsoLayout
from .svg_labels import _build_wan_label_lines, _escape_text
from .svg_theme import SvgOptions, SvgTheme


def _render_iso_wan_upstream(
    lines: list[str],
    wan_info: WanInfo,
    gateway_position: tuple[float, float],
    layout: IsoLayout,
    options: SvgOptions,
    theme: SvgTheme,
) -> None:
    """Render WAN upstream visualization (isometric view)."""
    gx, gy = gateway_position
    tile_w = layout.tile_width
    tile_h = layout.tile_height

    label_lines = _build_wan_label_lines(wan_info)
    font_size = max(options.font_size - 1, 8)

    globe_size = 40
    padding = 12
    line_height = font_size + 4
    max_text_width = max((len(line) for line in label_lines), default=10) * font_size * 0.55
    box_width = max(globe_size + padding * 2, max_text_width + padding * 2)
    box_height = globe_size + len(label_lines) * line_height + padding * 3

    box_x = gx + tile_w + 60
    box_y = gy - tile_h / 2 - box_height / 2 + 38

    gateway_connect_x = gx + tile_w * 0.75
    gateway_connect_y = gy + tile_h * 0.25
    box_connect_x = box_x
    box_connect_y = box_y + box_height / 2

    lines.append('<g class="wan-upstream">')
    lines.append(
        f'<path d="M {gateway_connect_x} {gateway_connect_y} '
        f'L {box_connect_x} {box_connect_y}" '
        f'stroke="#0288d1" stroke-width="3" fill="none" '
        f'stroke-linecap="round" opacity="0.8"/>'
    )
    lines.append(
        f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
        f'rx="8" ry="8" fill="{theme.wan_background}" stroke="{theme.wan_globe[1]}" stroke-width="2"/>'
    )

    globe_cx = box_x + box_width / 2
    globe_cy = box_y + padding + globe_size / 2
    globe_r = globe_size / 2 - 2
    lines.append(f'<g transform="translate({globe_cx}, {globe_cy})">')
    lines.append(
        f'<circle cx="0" cy="0" r="{globe_r}" fill="none" '
        f'stroke="url(#iso-globe)" stroke-width="2"/>'
    )
    lines.append(
        f'<ellipse cx="0" cy="0" rx="{globe_r * 0.35}" ry="{globe_r}" '
        f'fill="none" stroke="url(#iso-globe)" stroke-width="1.5"/>'
    )
    lines.append(
        f'<line x1="{-globe_r}" y1="0" x2="{globe_r}" y2="0" '
        f'stroke="url(#iso-globe)" stroke-width="1.5"/>'
    )
    lines.append(
        f'<ellipse cx="0" cy="{-globe_r * 0.5}" rx="{globe_r * 0.87}" ry="{globe_r * 0.2}" '
        f'fill="none" stroke="url(#iso-globe)" stroke-width="1"/>'
    )
    lines.append(
        f'<ellipse cx="0" cy="{globe_r * 0.5}" rx="{globe_r * 0.87}" ry="{globe_r * 0.2}" '
        f'fill="none" stroke="url(#iso-globe)" stroke-width="1"/>'
    )
    lines.append("</g>")

    text_x = box_x + box_width / 2
    text_y = box_y + padding + globe_size + padding + font_size
    for i, label_text in enumerate(label_lines):
        y = text_y + i * line_height
        lines.append(
            f'<text x="{text_x}" y="{y}" text-anchor="middle" '
            f'fill="{theme.text_primary}" font-size="{font_size}">'
            f"{_escape_text(label_text)}</text>"
        )

    lines.append("</g>")


def _expand_viewbox_for_wan(
    width: float,
    height: float,
    wan_info: WanInfo,
    node_types: dict[str, str],
    positions: dict[str, tuple[float, float]],
    layout: IsoLayout,
    options: SvgOptions,
) -> tuple[float, float]:
    """Expand viewBox dimensions to fit the WAN upstream box if needed."""
    gateway_name = next((name for name, node_type in node_types.items() if node_type == "gateway"), None)
    if not gateway_name or gateway_name not in positions:
        return width, height

    gx, gy = positions[gateway_name]
    label_lines = _build_wan_label_lines(wan_info)
    font_size = max(options.font_size - 1, 8)
    globe_size = 40
    padding = 12
    line_height = font_size + 4
    max_text_width = max((len(line) for line in label_lines), default=10) * font_size * 0.55
    box_width = max(globe_size + padding * 2, max_text_width + padding * 2)
    box_height = globe_size + len(label_lines) * line_height + padding * 3

    box_right = gx + layout.tile_width + 60 + box_width + padding
    box_top = gy - layout.tile_height / 2 - box_height / 2 + 38
    box_bottom = box_top + box_height + padding

    return max(width, box_right), max(height, box_bottom)


def _expand_viewbox_for_overlays(
    width: float,
    height: float,
    *,
    wan_info: WanInfo | None,
    vpn_tunnels: list[VpnTunnel] | None,
    node_types: dict[str, str],
    positions: dict[str, tuple[float, float]],
    layout: IsoLayout,
    options: SvgOptions,
) -> tuple[float, float]:
    if wan_info:
        width, height = _expand_viewbox_for_wan(
            width, height, wan_info, node_types, positions, layout, options
        )
    if vpn_tunnels:
        width = width + 200
        height = height + 100
    return width, height


def _find_gateway_position(
    node_types: dict[str, str],
    positions: dict[str, tuple[float, float]],
) -> tuple[float, float] | None:
    for name, node_type in node_types.items():
        if node_type == "gateway" and name in positions:
            return positions[name]
    return None
