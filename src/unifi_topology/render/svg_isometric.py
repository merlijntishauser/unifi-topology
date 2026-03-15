"""Isometric SVG rendering for network diagrams."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from ..model.topology import Edge, VpnTunnel, WanInfo
from . import _svg_iso_overlays
from ._svg_render_common import finish_svg_document, render_at_gateway, start_svg_document
from .svg_icons import _build_decal_colors, _load_isometric_icons
from .svg_iso_edges import _render_iso_edges
from .svg_iso_geometry import IsoLayout, _iso_project, _iso_project_center
from .svg_iso_nodes import _render_iso_nodes
from .svg_theme import DEFAULT_THEME, SvgOptions, SvgTheme
from .svg_vpn import _render_iso_vpn_tunnels

IsoGroupBounds = _svg_iso_overlays.IsoGroupBounds
_compute_iso_group_bounds = _svg_iso_overlays._compute_iso_group_bounds
_expand_viewbox_for_overlays = _svg_iso_overlays._expand_viewbox_for_overlays
_expand_viewbox_for_wan = _svg_iso_overlays._expand_viewbox_for_wan
_find_gateway_position = _svg_iso_overlays._find_gateway_position
_render_grouped_boundaries = _svg_iso_overlays._render_grouped_boundaries
_render_iso_group_boundaries = _svg_iso_overlays._render_iso_group_boundaries
_render_iso_wan_upstream = _svg_iso_overlays._render_iso_wan_upstream
_iso_group_parallelogram = _svg_iso_overlays._iso_group_parallelogram

# Re-export IsoLayout for external consumers
__all__ = ["IsoLayout", "render_svg_isometric"]

# Isometric layout constants (module-level for discoverability)
_ISO_NW_PADDING = 300  # North-west padding for iso layout
_ISO_VIEWPORT_EXPAND = 400  # Viewport expansion around content
_ISO_GRID_EXTENT_PAD = 36  # Grid extent padding beyond content
_ISO_GROUP_LABEL_SIZE = 48  # Font size for group boundary labels
_ISO_PERSPECTIVE_ANGLE = 30  # Isometric perspective angle in degrees


@dataclass(frozen=True)
class IsoLayoutPositions:
    layout: IsoLayout
    grid_positions: dict[str, tuple[float, float]]
    positions: dict[str, tuple[float, float]]
    width: float
    height: float
    offset_x: float
    offset_y: float


def _iso_layout(options: SvgOptions) -> IsoLayout:
    tile_width = options.node_width * 1.5
    iso_angle = math.radians(30.0)
    tile_height = tile_width * math.tan(iso_angle)
    step_width = tile_width
    step_height = tile_height
    grid_spacing_x = max(2, 1 + int(round(options.h_gap / max(tile_width, 1))))
    grid_spacing_y = max(2, 1 + int(round(options.v_gap / max(tile_height, 1))))
    padding = float(options.padding)
    tile_y_offset = tile_height / 2
    extra_pad = max(12.0, tile_width * 0.35)
    return IsoLayout(
        iso_angle=iso_angle,
        tile_width=tile_width,
        tile_height=tile_height,
        step_width=step_width,
        step_height=step_height,
        grid_spacing_x=grid_spacing_x,
        grid_spacing_y=grid_spacing_y,
        padding=padding,
        tile_y_offset=tile_y_offset,
        extra_pad=extra_pad,
    )


def _project_iso_positions(
    layout: IsoLayout,
    positions_index: Mapping[str, float],
    levels: Mapping[str, int],
) -> tuple[dict[str, tuple[float, float]], dict[str, tuple[float, float]]]:
    grid_positions: dict[str, tuple[float, float]] = {}
    positions: dict[str, tuple[float, float]] = {}
    for name, idx in positions_index.items():
        level = levels.get(name, 0)
        gx = round(idx * layout.grid_spacing_x)
        gy = round(float(level) * layout.grid_spacing_y)
        grid_positions[name] = (float(gx), float(gy))
        positions[name] = _iso_project_center(layout, float(gx), float(gy))
    return grid_positions, positions


def _position_extents(
    positions: dict[str, tuple[float, float]],
) -> tuple[float, float, float, float]:
    if not positions:
        return 0.0, 0.0, 0.0, 0.0
    return (
        min(x for x, _ in positions.values()),
        min(y for _, y in positions.values()),
        max(x for x, _ in positions.values()),
        max(y for _, y in positions.values()),
    )


def _iso_offsets(
    layout: IsoLayout,
    min_x: float,
    min_y: float,
) -> tuple[float, float]:
    return (
        -min_x + layout.padding + _ISO_NW_PADDING,
        -min_y + layout.padding + layout.tile_y_offset + _ISO_NW_PADDING,
    )


def _apply_iso_offsets(
    positions: dict[str, tuple[float, float]],
    offset_x: float,
    offset_y: float,
) -> dict[str, tuple[float, float]]:
    return {name: (x + offset_x, y + offset_y) for name, (x, y) in positions.items()}


def _iso_viewport_size(
    layout: IsoLayout,
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
) -> tuple[float, float]:
    viewport_expand = _ISO_VIEWPORT_EXPAND
    width = (
        max_x
        - min_x
        + layout.tile_width
        + layout.padding * 2
        + layout.extra_pad
        + viewport_expand
        + _ISO_NW_PADDING
    )
    height = (
        max_y
        - min_y
        + layout.tile_height
        + layout.padding * 2
        + layout.tile_y_offset
        + layout.extra_pad
        + viewport_expand
        + _ISO_NW_PADDING
    )
    return width, height


def _iso_layout_positions(
    edges: list[Edge],
    node_types: dict[str, str],
    options: SvgOptions,
) -> IsoLayoutPositions:
    from .svg_layout import _tree_layout_indices

    layout = _iso_layout(options)
    positions_index, levels = _tree_layout_indices(edges, node_types)
    grid_positions, positions = _project_iso_positions(layout, positions_index, levels)
    min_x, min_y, max_x, max_y = _position_extents(positions)
    offset_x, offset_y = _iso_offsets(layout, min_x, min_y)
    width, height = _iso_viewport_size(layout, min_x, min_y, max_x, max_y)
    return IsoLayoutPositions(
        layout=layout,
        grid_positions=grid_positions,
        positions=_apply_iso_offsets(positions, offset_x, offset_y),
        width=width,
        height=height,
        offset_x=offset_x,
        offset_y=offset_y,
    )


def _iso_grid_extents(
    grid_positions: dict[str, tuple[float, float]],
) -> tuple[int, int, int, int] | None:
    if not grid_positions:
        return None
    min_gx = min(gx for gx, _ in grid_positions.values())
    max_gx = max(gx for gx, _ in grid_positions.values())
    min_gy = min(gy for _, gy in grid_positions.values())
    max_gy = max(gy for _, gy in grid_positions.values())
    return (
        int(math.floor(min_gx)) - _ISO_GRID_EXTENT_PAD,
        int(math.ceil(max_gx)) + _ISO_GRID_EXTENT_PAD,
        int(math.floor(min_gy)) - _ISO_GRID_EXTENT_PAD,
        int(math.ceil(max_gy)) + _ISO_GRID_EXTENT_PAD,
    )


def _iso_grid_line(
    layout: IsoLayout,
    start: tuple[float, float],
    end: tuple[float, float],
    grid_color: str,
) -> str:
    x1, y1 = _iso_project(layout, *start)
    x2, y2 = _iso_project(layout, *end)
    x1 += layout.padding
    y1 += layout.padding
    x2 += layout.padding
    y2 += layout.padding
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{grid_color}" stroke-width="0.6"/>'
    )


def _iso_grid_lines(
    grid_positions: dict[str, tuple[float, float]],
    layout: IsoLayout,
    grid_color: str = "#efefef",
) -> list[str]:
    extents = _iso_grid_extents(grid_positions)
    if extents is None:
        return []
    gx_start, gx_end, gy_start, gy_end = extents
    grid_lines: list[str] = []
    for gx in range(gx_start, gx_end + 1):
        grid_lines.append(
            _iso_grid_line(layout, (float(gx), float(gy_start)), (float(gx), float(gy_end)), grid_color)
        )
    for gy in range(gy_start, gy_end + 1):
        grid_lines.append(
            _iso_grid_line(layout, (float(gx_start), float(gy)), (float(gx_end), float(gy)), grid_color)
        )
    return grid_lines

def _render_iso_grid(
    lines: list[str],
    grid_positions: dict[str, tuple[float, float]],
    layout: IsoLayout,
    theme: SvgTheme,
) -> None:
    grid_lines = _iso_grid_lines(grid_positions, layout, theme.grid_color)
    if grid_lines:
        lines.append('<g class="iso-grid" opacity="0.7">')
        lines.extend(grid_lines)
        lines.append("</g>")


def render_svg_isometric(
    edges: list[Edge],
    *,
    node_types: dict[str, str],
    options: SvgOptions | None = None,
    theme: SvgTheme = DEFAULT_THEME,
    groups: dict[str, list[str]] | None = None,
    group_order: list[str] | None = None,
    group_vlan_ids: dict[str, int] | None = None,
    wan_info: WanInfo | None = None,
    vpn_tunnels: list[VpnTunnel] | None = None,
) -> str:
    """Render an isometric (2.5D) SVG network diagram.

    Same interface as :func:`~unifi_network_maps.render.render_svg` but produces
    a 30-degree isometric projection with 3D-style device tiles and grid floor.
    """
    options = options or SvgOptions()
    per_type_decals = _build_decal_colors(theme)
    icons = _load_isometric_icons(theme.icon_set, theme.icon_decal, per_type_decals)
    layout_positions = _iso_layout_positions(edges, node_types, options)
    layout = layout_positions.layout
    grid_positions = layout_positions.grid_positions
    positions = layout_positions.positions

    view_width, view_height = _expand_viewbox_for_overlays(
        layout_positions.width,
        layout_positions.height,
        wan_info=wan_info,
        vpn_tunnels=vpn_tunnels,
        node_types=node_types,
        positions=positions,
        layout=layout,
        options=options,
    )

    out_width = options.width or int(view_width)
    out_height = options.height or int(view_height)

    lines = start_svg_document(
        width=view_width,
        height=view_height,
        out_width=out_width,
        out_height=out_height,
        theme=theme,
        options=options,
        defs_prefix="iso",
        iso=True,
    )

    if options.layout_mode == "grouped" and groups:
        _render_grouped_boundaries(
            lines,
            grid_positions,
            groups,
            group_order,
            group_vlan_ids,
            layout,
            layout_positions.offset_x,
            layout_positions.offset_y,
            options,
            theme,
        )

    _render_iso_grid(lines, grid_positions, layout, theme)

    node_port_labels: dict[str, str] = {}
    node_port_prefix: dict[str, str] = {}
    _render_iso_edges(
        lines,
        edges,
        positions=positions,
        grid_positions=grid_positions,
        node_types=node_types,
        layout=layout,
        theme=theme,
        offset_x=layout_positions.offset_x,
        offset_y=layout_positions.offset_y,
        node_port_labels=node_port_labels,
        node_port_prefix=node_port_prefix,
    )
    _render_iso_nodes(
        lines,
        positions=positions,
        node_types=node_types,
        icons=icons,
        options=options,
        layout=layout,
        node_port_labels=node_port_labels,
        node_port_prefix=node_port_prefix,
        theme=theme,
    )

    render_at_gateway(
        lines=lines,
        content=wan_info,
        node_types=node_types,
        positions=positions,
        find_gateway_position=_find_gateway_position,
        render=lambda doc_lines, info, gateway_pos: _render_iso_wan_upstream(
            doc_lines, info, gateway_pos, layout, options, theme
        ),
    )
    render_at_gateway(
        lines=lines,
        content=vpn_tunnels,
        node_types=node_types,
        positions=positions,
        find_gateway_position=_find_gateway_position,
        render=lambda doc_lines, tunnels, gateway_pos: _render_iso_vpn_tunnels(
            doc_lines,
            tunnels,
            gateway_pos,
            layout.tile_width,
            layout.tile_height,
            options,
            theme,
        ),
    )

    return finish_svg_document(lines)
