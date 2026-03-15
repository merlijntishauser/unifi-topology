"""Private helpers for isometric overlays and grouped boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape as _escape_html

from ..model.topology import VpnTunnel, WanInfo
from .svg_iso_geometry import IsoLayout, _iso_project
from .svg_labels import _build_wan_label_lines, _escape_text
from .svg_layout import _build_node_to_group_map, _resolve_group_order
from .svg_theme import SvgOptions, SvgTheme
from .svg_wan import _vlan_group_colors

_ISO_GROUP_LABEL_SIZE = 48
_ISO_PERSPECTIVE_ANGLE = 30


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


@dataclass(frozen=True)
class IsoGroupBounds:
    name: str
    points: list[tuple[float, float]]
    label_x: float
    label_y: float


def _compute_iso_group_bounds(
    grid_positions: dict[str, tuple[float, float]],
    groups: dict[str, list[str]],
    group_order: list[str] | None,
    layout: IsoLayout,
    offset_x: float,
    offset_y: float,
    options: SvgOptions,
) -> list[IsoGroupBounds]:
    """Compute isometric group bounds as parallelograms aligned with grid."""
    ordered_groups = _resolve_group_order(groups, group_order)
    node_to_group = _build_node_to_group_map(groups)
    bounds_list: list[IsoGroupBounds] = []
    padding = options.group_padding / layout.step_width + 0.5

    for group_name in ordered_groups:
        group_grid = {
            node: pos for node, pos in grid_positions.items() if node_to_group.get(node) == group_name
        }
        if not group_grid:
            continue
        bounds_list.append(
            _iso_group_parallelogram(group_name, group_grid, layout, offset_x, offset_y, padding)
        )
    return bounds_list


def _iso_group_parallelogram(
    name: str,
    group_grid: dict[str, tuple[float, float]],
    layout: IsoLayout,
    offset_x: float,
    offset_y: float,
    padding: float,
) -> IsoGroupBounds:
    """Create isometric parallelogram bounds from grid positions."""
    gxs = [gx for gx, _ in group_grid.values()]
    gys = [gy for _, gy in group_grid.values()]

    if len(group_grid) == 1:
        node_half = 0.8
        center_gx = min(gxs) + 1.45
        center_gy = min(gys) + 0.45
        min_gx = center_gx - node_half
        max_gx = center_gx + node_half
        min_gy = center_gy - node_half
        max_gy = center_gy + node_half
    else:
        min_gx = min(gxs) - padding
        max_gx = max(gxs) + layout.grid_spacing_x + padding
        min_gy = min(gys) - padding
        max_gy = max(gys) + layout.grid_spacing_y + padding

    corners_grid = [
        (min_gx, min_gy),
        (max_gx, min_gy),
        (max_gx, max_gy),
        (min_gx, max_gy),
    ]
    points = [
        (_iso_project(layout, gx, gy)[0] + offset_x, _iso_project(layout, gx, gy)[1] + offset_y)
        for gx, gy in corners_grid
    ]

    top_x, top_y = points[0]
    right_x, right_y = points[1]
    label_x = top_x + (right_x - top_x) * 0.15 - 30
    label_y = top_y + (right_y - top_y) * 0.15 - 20
    return IsoGroupBounds(name=name, points=points, label_x=label_x, label_y=label_y)


def _render_iso_group_boundaries(
    lines: list[str],
    bounds_list: list[IsoGroupBounds],
    theme: SvgTheme,
    *,
    group_vlan_ids: dict[str, int] | None = None,
) -> None:
    """Render isometric group boundaries as parallelograms."""
    for bounds in bounds_list:
        group_attr = _escape_html(bounds.name, quote=True)
        fill, stroke = _vlan_group_colors(bounds.name, theme, group_vlan_ids)
        points_str = " ".join(f"{x},{y}" for x, y in bounds.points)
        lines.append(f'<g class="network-group" data-group-name="{group_attr}">')
        lines.append(
            f'<polygon class="group-boundary" points="{points_str}" '
            f'fill="{fill}" fill-opacity="0.35" '
            f'stroke="{stroke}" stroke-width="{theme.group_stroke_width}"/>'
        )
        label_text = _escape_text(bounds.name.capitalize())
        lx, ly = bounds.label_x, bounds.label_y
        label_transform = (
            f"translate({lx} {ly}) rotate({_ISO_PERSPECTIVE_ANGLE}) "
            f"skewX({_ISO_PERSPECTIVE_ANGLE}) translate({-lx} {-ly})"
        )
        lines.append(
            f'<text class="group-label" x="{lx}" y="{ly}" '
            f'font-size="{_ISO_GROUP_LABEL_SIZE}" font-weight="bold" fill="{stroke}" '
            f'stroke="#ffffff" stroke-width="2" paint-order="stroke fill" '
            f'opacity="0.7" transform="{label_transform}">'
            f"{label_text}</text>"
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


def _render_grouped_boundaries(
    lines: list[str],
    grid_positions: dict[str, tuple[float, float]],
    groups: dict[str, list[str]],
    group_order: list[str] | None,
    group_vlan_ids: dict[str, int] | None,
    layout: IsoLayout,
    offset_x: float,
    offset_y: float,
    options: SvgOptions,
    theme: SvgTheme,
) -> None:
    group_bounds_list = _compute_iso_group_bounds(
        grid_positions,
        groups,
        group_order,
        layout,
        offset_x,
        offset_y,
        options,
    )
    _render_iso_group_boundaries(lines, group_bounds_list, theme, group_vlan_ids=group_vlan_ids)
