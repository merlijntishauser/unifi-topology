"""Private helpers for isometric edge geometry and drawing."""

from __future__ import annotations

from ..model.topology import Edge
from . import _svg_edge_shared
from ._svg_iso_edge_labels import _record_iso_edge_labels
from .svg_iso_geometry import IsoLayout, _iso_project_center
from .svg_theme import SvgTheme

_edge_render_state = _svg_edge_shared._edge_render_state
_render_vlan_endpoint_markers = _svg_edge_shared._render_vlan_endpoint_markers


def _iso_front_anchor(
    layout: IsoLayout,
    *,
    gx: float,
    gy: float,
    offset_x: float,
    offset_y: float,
) -> tuple[float, float]:
    iso_x, iso_y = _iso_project_center(layout, gx, gy)
    cx = iso_x + offset_x + layout.tile_width / 2
    cy = iso_y + offset_y + layout.tile_height / 2
    return cx, cy


def _render_iso_vlan_striped_edge(
    lines: list[str],
    path: str,
    vlans: tuple[int, ...],
    theme: SvgTheme,
    base_width: int,
    is_wireless: bool,
    extra_attrs: str,
    opacity: float = 1.0,
) -> None:
    """Render an isometric edge with striped VLAN colors and glow effect."""
    _svg_edge_shared._render_vlan_striped_edge_generic(
        lines,
        path,
        vlans,
        theme,
        base_width,
        is_wireless,
        extra_attrs,
        opacity,
        segment_len=16,
        filter_id="iso-edge-glow",
        line_attrs='stroke-linecap="round" stroke-linejoin="round" ',
        wireless_dash=lambda gap_len: f"6 3 6 {gap_len + 1}",
    )


def _render_iso_poe_icon(
    lines: list[str],
    layout: IsoLayout,
    offset_x: float,
    offset_y: float,
    src_gx: float,
    src_gy: float,
    dst_gx: float,
    dst_gy: float,
    src_cx: float,
    src_cy: float,
    dst_cx: float,
    dst_cy: float,
    theme: SvgTheme,
    *,
    has_port_labels: bool = False,
    occupied: frozenset[tuple[int, int]] = frozenset(),
) -> None:
    """Render PoE icon on an edge path."""
    poe_size = 30
    seg_start_x, seg_start_y = _poe_segment_start(
        layout,
        offset_x=offset_x,
        offset_y=offset_y,
        src_gx=src_gx,
        src_gy=src_gy,
        dst_gx=dst_gx,
        dst_gy=dst_gy,
        src_cx=src_cx,
        src_cy=src_cy,
        occupied=occupied,
    )
    t = 0.15 if has_port_labels else 0.6
    icon_center_x = seg_start_x + t * (dst_cx - seg_start_x)
    icon_center_y = seg_start_y + t * (dst_cy - seg_start_y)
    icon_x = icon_center_x - poe_size / 2
    icon_y = icon_center_y - poe_size / 2
    lines.append(
        f'<use href="#iso-poe-bolt" x="{icon_x}" y="{icon_y}" '
        f'width="{poe_size}" height="{poe_size}" '
        f'fill="{theme.poe_fill}" stroke="{theme.poe_stroke}" stroke-width="1"/>'
    )


def occupied_cells(grid_positions: dict[str, tuple[float, float]]) -> frozenset[tuple[int, int]]:
    """Lattice cells that hold a node, so edges can be routed around them."""
    return frozenset((int(round(gx)), int(round(gy))) for gx, gy in grid_positions.values())


def _span(start: int, end: int) -> range:
    """The values strictly between two integers, in travel order."""
    step = 1 if end > start else -1
    return range(start + step, end, step)


def _cells_between(
    start: tuple[int, int],
    end: tuple[int, int],
) -> list[tuple[int, int]]:
    """Lattice cells strictly between two points on a shared grid axis."""
    (x0, y0), (x1, y1) = start, end
    if x0 == x1:
        return [(x0, y) for y in _span(y0, y1)]
    if y0 == y1:
        return [(x, y0) for x in _span(x0, x1)]
    return []


def _inclusive(start: int, end: int) -> range:
    """Every value from start to end, both ends included, in travel order."""
    step = 1 if end >= start else -1
    return range(start, end + step, step)


def _route_cost(
    src: tuple[int, int],
    corners: list[tuple[int, int]],
    dst: tuple[int, int],
    occupied: frozenset[tuple[int, int]],
) -> int:
    """How many occupied cells a route would be drawn over."""
    points = [src, *corners, dst]
    cells = list(corners)
    for start, end in zip(points, points[1:], strict=False):
        cells.extend(_cells_between(start, end))
    return sum(1 for cell in cells if cell in occupied and cell not in (src, dst))


def _candidate_routes(
    src: tuple[int, int],
    dst: tuple[int, int],
) -> list[list[tuple[int, int]]]:
    """Every axis-aligned route worth considering, as lists of corner cells.

    Two L shapes, differing only in which axis is travelled first, then the Z
    shapes that step sideways into a clear lane before completing the turn. All
    of them run along grid axes, so each leg projects to a true isometric line.
    """
    routes = [[(dst[0], src[1])], [(src[0], dst[1])]]
    routes += [[(mx, src[1]), (mx, dst[1])] for mx in _inclusive(src[0], dst[0])]
    routes += [[(src[0], my), (dst[0], my)] for my in _inclusive(src[1], dst[1])]
    return routes


def _route_score(
    src: tuple[int, int],
    dst: tuple[int, int],
    occupied: frozenset[tuple[int, int]],
    route: list[tuple[int, int]],
) -> tuple[int, int, float]:
    """Fewest nodes crossed, then fewest corners, then the most centred turn."""
    mid_x = (src[0] + dst[0]) / 2
    mid_y = (src[1] + dst[1]) / 2
    off_centre = min(abs(x - mid_x) + abs(y - mid_y) for x, y in route)
    return _route_cost(src, route, dst, occupied), len(route), off_centre


def _route_corners(
    src_gx: float,
    src_gy: float,
    dst_gx: float,
    dst_gy: float,
    occupied: frozenset[tuple[int, int]],
) -> list[tuple[float, float]]:
    """Corner cells for the clearest route between two nodes."""
    src = (int(round(src_gx)), int(round(src_gy)))
    dst = (int(round(dst_gx)), int(round(dst_gy)))
    best = min(
        _candidate_routes(src, dst),
        key=lambda route: _route_score(src, dst, occupied, route),
    )
    return [(float(x), float(y)) for x, y in best]


def _poe_segment_start(
    layout: IsoLayout,
    *,
    offset_x: float,
    offset_y: float,
    src_gx: float,
    src_gy: float,
    dst_gx: float,
    dst_gy: float,
    src_cx: float,
    src_cy: float,
    occupied: frozenset[tuple[int, int]] = frozenset(),
) -> tuple[float, float]:
    dx = dst_gx - src_gx
    dy = dst_gy - src_gy
    if dx == 0 or dy == 0:
        return src_cx, src_cy
    corner_gx, corner_gy = _route_corners(src_gx, src_gy, dst_gx, dst_gy, occupied)[0]
    return _iso_front_anchor(
        layout, gx=corner_gx, gy=corner_gy, offset_x=offset_x, offset_y=offset_y
    )


def _render_iso_standard_edge(
    lines: list[str],
    path: str,
    edge: Edge,
    width_px: int,
    base_attrs: str,
    opacity_attr: str,
) -> None:
    """Render a standard (non-VLAN) edge path."""
    color = "url(#iso-link-poe)" if edge.poe else "url(#iso-link-standard)"
    dash = ' stroke-dasharray="8 6"' if edge.wireless else ""
    lines.append(
        f'<path d="{path}" stroke="{color}" stroke-width="{width_px}" '
        f'fill="none" stroke-linecap="round" stroke-linejoin="round"{dash}{opacity_attr} '
        f"{base_attrs}/>"
    )


def _iso_edge_path(
    layout: IsoLayout,
    offset_x: float,
    offset_y: float,
    src_gx: float,
    src_gy: float,
    dst_gx: float,
    dst_gy: float,
    src_cx: float,
    src_cy: float,
    dst_cx: float,
    dst_cy: float,
    occupied: frozenset[tuple[int, int]] = frozenset(),
) -> list[str]:
    dx = dst_gx - src_gx
    dy = dst_gy - src_gy
    if dx == 0 or dy == 0:
        return [f"M {src_cx} {src_cy}", f"L {dst_cx} {dst_cy}"]
    corners = _route_corners(src_gx, src_gy, dst_gx, dst_gy, occupied)
    steps = [f"M {src_cx} {src_cy}"]
    for corner_gx, corner_gy in corners:
        cx, cy = _iso_front_anchor(
            layout, gx=corner_gx, gy=corner_gy, offset_x=offset_x, offset_y=offset_y
        )
        steps.append(f"L {cx} {cy}")
    steps.append(f"L {dst_cx} {dst_cy}")
    return steps


def _resolve_edge_coords(
    edge: Edge,
    grid_positions: dict[str, tuple[float, float]],
    layout: IsoLayout,
    offset_x: float,
    offset_y: float,
) -> tuple[float, float, float, float, float, float, float, float] | None:
    src_grid = grid_positions.get(edge.left)
    dst_grid = grid_positions.get(edge.right)
    if not src_grid or not dst_grid:
        return None
    src_gx, src_gy = float(src_grid[0]), float(src_grid[1])
    dst_gx, dst_gy = float(dst_grid[0]), float(dst_grid[1])
    src_cx, src_cy = _iso_front_anchor(
        layout, gx=src_gx, gy=src_gy, offset_x=offset_x, offset_y=offset_y
    )
    dst_cx, dst_cy = _iso_front_anchor(
        layout, gx=dst_gx, gy=dst_gy, offset_x=offset_x, offset_y=offset_y
    )
    return src_gx, src_gy, dst_gx, dst_gy, src_cx, src_cy, dst_cx, dst_cy


def _render_single_iso_edge(
    lines: list[str],
    edge: Edge,
    coords: tuple[float, float, float, float, float, float, float, float],
    *,
    node_types: dict[str, str],
    layout: IsoLayout,
    theme: SvgTheme,
    offset_x: float,
    offset_y: float,
    node_port_labels: dict[str, str],
    max_vlan_colors: int | None,
    occupied: frozenset[tuple[int, int]] = frozenset(),
) -> None:
    src_gx, src_gy, dst_gx, dst_gy, src_cx, src_cy, dst_cx, dst_cy = coords
    width_px = 5 if edge.poe else 4
    path = " ".join(
        _iso_edge_path(
            layout,
            offset_x,
            offset_y,
            src_gx,
            src_gy,
            dst_gx,
            dst_gy,
            src_cx,
            src_cy,
            dst_cx,
            dst_cy,
            occupied,
        )
    )
    state = _edge_render_state(edge, node_types, max_vlan_colors=max_vlan_colors)

    if state.display_vlans:
        _render_iso_vlan_striped_edge(
            lines,
            path,
            state.display_vlans,
            theme,
            width_px,
            edge.wireless,
            state.base_attrs,
            state.opacity,
        )
        marker_x = dst_cx + layout.tile_width * 0.3
        marker_y = dst_cy - layout.tile_height * 0.2
        _render_vlan_endpoint_markers(lines, marker_x, marker_y, state.display_vlans, theme)
    else:
        _render_iso_standard_edge(lines, path, edge, width_px, state.base_attrs, state.opacity_attr)

    if edge.poe:
        _render_iso_poe_icon(
            lines,
            layout,
            offset_x,
            offset_y,
            src_gx,
            src_gy,
            dst_gx,
            dst_gy,
            src_cx,
            src_cy,
            dst_cx,
            dst_cy,
            theme,
            has_port_labels=edge.right in node_port_labels,
            occupied=occupied,
        )


def _edge_occupancy(
    grid_positions: dict[str, tuple[float, float]],
    *,
    avoid_nodes: bool,
) -> frozenset[tuple[int, int]]:
    """Cells routing must avoid, or nothing when the option is off.

    With an empty set every candidate route scores zero, so the tie-break falls
    through to the fewest-corners, first-listed candidate -- which is the
    original gx-first elbow. Output is therefore unchanged by default.
    """
    if not avoid_nodes:
        return frozenset()
    return occupied_cells(grid_positions)


def _render_iso_edges(
    lines: list[str],
    edges: list[Edge],
    *,
    positions: dict[str, tuple[float, float]],
    grid_positions: dict[str, tuple[float, float]],
    node_types: dict[str, str],
    layout: IsoLayout,
    theme: SvgTheme,
    offset_x: float,
    offset_y: float,
    node_port_labels: dict[str, str],
    node_port_prefix: dict[str, str],
    max_vlan_colors: int | None = None,
    node_names: dict[str, str] | None = None,
    avoid_nodes: bool = False,
) -> None:
    _record_iso_edge_labels(edges, node_types, node_port_labels, node_port_prefix, node_names)
    occupied = _edge_occupancy(grid_positions, avoid_nodes=avoid_nodes)
    for edge in sorted(edges, key=lambda item: item.poe):
        if edge.left not in positions or edge.right not in positions:
            continue
        coords = _resolve_edge_coords(edge, grid_positions, layout, offset_x, offset_y)
        if not coords:
            continue
        _render_single_iso_edge(
            lines,
            edge,
            coords,
            node_types=node_types,
            layout=layout,
            theme=theme,
            offset_x=offset_x,
            offset_y=offset_y,
            node_port_labels=node_port_labels,
            max_vlan_colors=max_vlan_colors,
            occupied=occupied,
        )
