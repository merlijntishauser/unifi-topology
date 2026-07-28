"""Where an isometric edge turns, in grid space.

Kept apart from drawing because the layout needs it too: the canvas is sized
before edges are drawn, and a corner can project outside the box the nodes span.
If the two sides disagreed about which edges have a corner and where, the corner
would fall outside the viewBox and the edge would render clipped.
"""

from __future__ import annotations


def occupied_cells(grid_positions: dict[str, tuple[float, float]]) -> frozenset[tuple[int, int]]:
    """Lattice cells that hold a node, so edges can be routed around them."""
    return frozenset((int(round(gx)), int(round(gy))) for gx, gy in grid_positions.values())


def edge_occupancy(
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


def _span(start: int, end: int) -> range:
    """The values strictly between two integers, in travel order."""
    step = 1 if end > start else -1
    return range(start + step, end, step)


def _inclusive(start: int, end: int) -> range:
    """Every value from start to end, both ends included, in travel order."""
    step = 1 if end >= start else -1
    return range(start, end + step, step)


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


def route_corners(
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


def edge_corners(
    src_grid: tuple[float, float],
    dst_grid: tuple[float, float],
    occupied: frozenset[tuple[int, int]],
) -> list[tuple[float, float]]:
    """Corners an edge turns through -- none when it runs along one grid axis."""
    if src_grid[0] == dst_grid[0] or src_grid[1] == dst_grid[1]:
        return []
    return route_corners(src_grid[0], src_grid[1], dst_grid[0], dst_grid[1], occupied)


def _blocked(
    src_grid: tuple[float, float],
    corners: list[tuple[float, float]],
    dst_grid: tuple[float, float],
    occupied: frozenset[tuple[int, int]],
) -> bool:
    """Whether even the best route is still drawn over some node.

    A hub's grid diagonals run through its own client field, so every
    two-corner candidate between certain nodes crosses a tile: the minimum is
    not always zero.
    """
    if not occupied:
        return False
    src = (int(round(src_grid[0])), int(round(src_grid[1])))
    dst = (int(round(dst_grid[0])), int(round(dst_grid[1])))
    cells = [(int(round(x)), int(round(y))) for x, y in corners]
    return _route_cost(src, cells, dst, occupied) > 0


def edge_route(
    src_grid: tuple[float, float],
    dst_grid: tuple[float, float],
    occupied: frozenset[tuple[int, int]],
    lane_offset: float = 0.0,
) -> list[tuple[float, float]]:
    """Every grid point of an edge, endpoints included, on its final lane.

    The single source of truth for drawing and canvas sizing. Nodes sit on even
    grid coordinates, so when the best route is still blocked the whole run is
    shifted one unit onto the adjacent half-lane -- which can never hold a node
    -- with short jogs joining the true endpoints. Every leg stays grid-aligned
    and projects to a true isometric line.
    """
    corners = edge_corners(src_grid, dst_grid, occupied)
    if _blocked(src_grid, corners, dst_grid, occupied):
        # Node cells all have integer coordinates, so the half-integer lanes
        # can never hold one. An integer shift is no escape at all: it lands on
        # integer lanes again, and a leg that sat safely on an odd column moves
        # onto an even one -- straight through whatever node lives there. The
        # fan offset is compressed so the total stays clear of whole lanes.
        shift = 0.5 + lane_offset * 0.25
    else:
        shift = lane_offset
    return offset_route(src_grid, corners, dst_grid, shift)


# Parallel lane offsets, in grid units, cycled across edges that share a source.
# Superimposed fan-outs read as one wire chaining every node it passes; small
# offsets separate them into distinct traces that visibly end where they end.
_OFFSET_CYCLE = (0.0, 0.3, -0.3, 0.5, -0.5, 0.15, -0.15)


def edge_lane_offsets(edges) -> list[float]:
    """A deterministic lane offset per edge, spreading edges that share a source."""
    seen: dict[str, int] = {}
    offsets: list[float] = []
    for edge in edges:
        index = seen.get(edge.left, 0)
        seen[edge.left] = index + 1
        offsets.append(_OFFSET_CYCLE[index % len(_OFFSET_CYCLE)])
    return offsets


def _jog(point: tuple[float, float], toward: tuple[float, float], offset: float):
    """Shift *point* onto the offset lane of the leg leading to *toward*."""
    if abs(point[1] - toward[1]) < 1e-9:
        return (point[0], point[1] + offset)
    return (point[0] + offset, point[1])


def offset_route(
    src: tuple[float, float],
    corners: list[tuple[float, float]],
    dst: tuple[float, float],
    offset: float,
) -> list[tuple[float, float]]:
    """The grid points of a route shifted onto a parallel lane.

    Endpoints stay put; short perpendicular stubs join them to the shifted
    lane, so every leg stays grid-aligned and still projects to a true
    isometric line.
    """
    if not offset:
        return [src, *corners, dst]
    if not corners:
        return [src, _jog(src, dst, offset), _jog(dst, src, offset), dst]
    shifted = [(x + offset, y + offset) for x, y in corners]
    return [src, _jog(src, corners[0], offset), *shifted, _jog(dst, corners[-1], offset), dst]
