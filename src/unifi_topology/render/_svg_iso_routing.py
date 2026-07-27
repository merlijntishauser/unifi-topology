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
    """Corners an edge actually turns through -- none when it runs along one axis.

    The single source of truth for both drawing and canvas sizing.
    """
    if src_grid[0] == dst_grid[0] or src_grid[1] == dst_grid[1]:
        return []
    return route_corners(src_grid[0], src_grid[1], dst_grid[0], dst_grid[1], occupied)
