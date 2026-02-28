"""VPN tunnel rendering for SVG diagrams."""

from __future__ import annotations

from ..model.topology import VpnTunnel
from .svg_labels import _build_vpn_label_lines, _escape_text
from .svg_theme import SvgOptions, SvgTheme


def _vpn_status_colors(tunnels: list[VpnTunnel], theme: SvgTheme) -> tuple[str, str]:
    """Return (stroke, gradient_id) based on tunnel status.

    Green when all tunnels are up, red when any is down.
    """
    all_up = all(t.up for t in tunnels)
    if all_up:
        return theme.vpn_up[1], "vpn-up"
    return theme.vpn_down[1], "vpn-down"


def _vpn_box_dimensions(
    label_lines: list[str],
    font_size: int,
) -> tuple[int, int, int, float, float]:
    """Calculate VPN box dimensions from label content.

    Returns (icon_size, padding, line_height, box_width, box_height).
    """
    icon_size = 30
    padding = 10
    line_height = font_size + 4
    max_text_width = max((len(line) for line in label_lines), default=10) * font_size * 0.55
    box_width = max(icon_size + padding * 2, max_text_width + padding * 2)
    box_height = icon_size + len(label_lines) * line_height + padding * 3
    return icon_size, padding, line_height, box_width, box_height


def _render_vpn_icon(
    lines: list[str],
    cx: float,
    cy: float,
    size: float,
    gradient_id: str,
) -> None:
    """Render a lock/shield VPN icon."""
    half = size / 2
    # Shield shape path
    lines.append(f'<g transform="translate({cx}, {cy})">')
    # Outer shield
    shield_h = half * 1.1
    lines.append(
        f'<path d="M 0 {-shield_h} '
        f"L {half * 0.8} {-shield_h * 0.5} "
        f"L {half * 0.8} {shield_h * 0.3} "
        f"Q {half * 0.6} {shield_h} 0 {shield_h * 1.1} "
        f"Q {-half * 0.6} {shield_h} {-half * 0.8} {shield_h * 0.3} "
        f'L {-half * 0.8} {-shield_h * 0.5} Z" '
        f'fill="url(#{gradient_id})" fill-opacity="0.3" '
        f'stroke="url(#{gradient_id})" stroke-width="1.5"/>'
    )
    # Lock body inside shield
    lock_w = half * 0.45
    lock_h = half * 0.4
    lock_y = half * 0.05
    lines.append(
        f'<rect x="{-lock_w}" y="{lock_y}" width="{lock_w * 2}" height="{lock_h}" '
        f'rx="2" fill="url(#{gradient_id})"/>'
    )
    # Lock shackle
    shackle_r = lock_w * 0.7
    lines.append(
        f'<path d="M {-shackle_r} {lock_y} '
        f'A {shackle_r} {shackle_r} 0 0 1 {shackle_r} {lock_y}" '
        f'fill="none" stroke="url(#{gradient_id})" stroke-width="1.5"/>'
    )
    lines.append("</g>")


def _render_vpn_tunnels(
    lines: list[str],
    tunnels: list[VpnTunnel],
    gateway_position: tuple[float, float],
    options: SvgOptions,
    theme: SvgTheme,
) -> None:
    """Render VPN tunnel visualization (orthogonal view).

    Positions a VPN box below the gateway node, connected by a dashed line.
    """
    gx, gy = gateway_position
    font_size = options.font_size
    label_lines = _build_vpn_label_lines(tunnels)
    stroke_color, gradient_id = _vpn_status_colors(tunnels, theme)
    icon_size, padding, line_height, box_width, box_height = _vpn_box_dimensions(
        label_lines, font_size
    )

    # Position box below the gateway
    box_x = gx + options.node_width / 2 - box_width / 2
    box_y = gy + options.node_height + 30

    # Connection points
    gw_cx = gx + options.node_width / 2
    gw_cy = gy + options.node_height
    box_cx = box_x + box_width / 2
    box_cy = box_y

    lines.append('<g class="vpn-tunnels">')

    # Dashed connector line from gateway to VPN box
    lines.append(
        f'<path d="M {gw_cx} {gw_cy} L {box_cx} {box_cy}" '
        f'stroke="{stroke_color}" stroke-width="2" fill="none" '
        f'stroke-dasharray="6,3" stroke-linecap="round" opacity="0.8"/>'
    )

    # Box background
    lines.append(
        f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
        f'rx="6" ry="6" fill="{theme.vpn_background}" '
        f'stroke="{stroke_color}" stroke-width="1.5"/>'
    )

    # Shield icon
    icon_cx = box_x + box_width / 2
    icon_cy = box_y + padding + icon_size / 2
    _render_vpn_icon(lines, icon_cx, icon_cy, icon_size, gradient_id)

    # Labels
    text_x = box_x + box_width / 2
    text_y = box_y + padding + icon_size + padding + font_size
    for i, label_text in enumerate(label_lines):
        y = text_y + i * line_height
        lines.append(
            f'<text x="{text_x}" y="{y}" text-anchor="middle" '
            f'fill="{theme.text_primary}" font-size="{font_size}">'
            f"{_escape_text(label_text)}</text>"
        )

    lines.append("</g>")


def _render_iso_vpn_tunnels(
    lines: list[str],
    tunnels: list[VpnTunnel],
    gateway_position: tuple[float, float],
    tile_width: float,
    tile_height: float,
    options: SvgOptions,
    theme: SvgTheme,
) -> None:
    """Render VPN tunnel visualization (isometric view).

    Positions a VPN box to the south-west of the gateway.
    """
    gx, gy = gateway_position
    font_size = max(options.font_size - 1, 8)
    label_lines = _build_vpn_label_lines(tunnels)
    stroke_color, gradient_id = _vpn_status_colors(tunnels, theme)

    # Calculate box dimensions
    icon_size = 34
    padding_val = 12
    line_height = font_size + 4
    max_text_width = max((len(line) for line in label_lines), default=10) * font_size * 0.55
    box_width = max(icon_size + padding_val * 2, max_text_width + padding_val * 2)
    box_height = icon_size + len(label_lines) * line_height + padding_val * 3

    # Use iso- prefix for gradient references
    iso_gradient_id = f"iso-{gradient_id}"

    # Position box to the south-west (opposite of WAN which is to the east)
    box_x = gx - box_width - 60
    box_y = gy + tile_height / 2 - box_height / 2 + 38

    # Connection point on gateway (west edge of tile)
    gateway_connect_x = gx + tile_width * 0.25
    gateway_connect_y = gy + tile_height * 0.75

    # Connection point on box (right edge, middle)
    box_connect_x = box_x + box_width
    box_connect_y = box_y + box_height / 2

    lines.append('<g class="vpn-tunnels">')

    # Dashed connector line
    lines.append(
        f'<path d="M {gateway_connect_x} {gateway_connect_y} '
        f'L {box_connect_x} {box_connect_y}" '
        f'stroke="{stroke_color}" stroke-width="3" fill="none" '
        f'stroke-dasharray="8,4" stroke-linecap="round" opacity="0.8"/>'
    )

    # Box background
    lines.append(
        f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
        f'rx="8" ry="8" fill="{theme.vpn_background}" '
        f'stroke="{stroke_color}" stroke-width="2"/>'
    )

    # Shield icon
    icon_cx = box_x + box_width / 2
    icon_cy = box_y + padding_val + icon_size / 2
    _render_vpn_icon(lines, icon_cx, icon_cy, icon_size, iso_gradient_id)

    # Labels
    text_x = box_x + box_width / 2
    text_y = box_y + padding_val + icon_size + padding_val + font_size
    for i, label_text in enumerate(label_lines):
        y = text_y + i * line_height
        lines.append(
            f'<text x="{text_x}" y="{y}" text-anchor="middle" '
            f'fill="{theme.text_primary}" font-size="{font_size}">'
            f"{_escape_text(label_text)}</text>"
        )

    lines.append("</g>")


def _vpn_box_height_estimate(tunnel_count: int, font_size: int) -> float:
    """Estimate VPN box height for layout offset calculations."""
    icon_size = 30
    padding = 10
    line_height = font_size + 4
    return icon_size + tunnel_count * line_height + padding * 3 + 30
