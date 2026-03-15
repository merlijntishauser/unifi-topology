"""Private helpers for isometric grouped boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape as _escape_html

from .svg_iso_geometry import IsoLayout, _iso_project
from .svg_labels import _escape_text
from .svg_layout import _build_node_to_group_map, _resolve_group_order
from .svg_theme import SvgOptions, SvgTheme
from .svg_wan import _vlan_group_colors

_ISO_GROUP_LABEL_SIZE = 48
_ISO_PERSPECTIVE_ANGLE = 30


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
            node: pos
            for node, pos in grid_positions.items()
            if node_to_group.get(node) == group_name
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
