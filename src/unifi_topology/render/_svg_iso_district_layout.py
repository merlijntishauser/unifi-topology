"""Compact 'district' layout for isometric diagrams.

The default tree layout assigns one axis to sibling order and the other to tree
depth. Real networks are shallow and wide, so that produces a long diagonal
strip: a 22x4 grid for 15 nodes, drawn as a thin line across a mostly empty
canvas. Averaging child indices also lets two parents land on the same cell,
which stacks nodes on top of each other.

This layout instead treats the ground plane as a plane. Each hub (a device with
children) and its leaf children form a *district* -- a compact rectangular block
-- and districts are packed into shelves sized to keep the whole composition
close to a target screen aspect.

Coordinates are built in a screen-aligned (lateral, spine) lattice and converted
to isometric grid coordinates at the end. The isometric projection maps grid
(1, 1) to straight down the screen and (1, -1) to straight right, so::

    gx = spine + lateral
    gy = spine - lateral

places nodes on a lattice whose axes line up with the viewer's, while the tiles
themselves stay diamond-shaped.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..model.topology import Edge
from ._svg_tree_layout import (
    _build_children_maps,
    _layout_nodeset,
    _resolve_roots,
    _sort_children,
    _sort_key_for_nodes,
)

# Screen height of one spine step divided by screen width of one lateral step.
# Equal to tan(30 degrees) for a true isometric projection.
_TILE_ASPECT = math.tan(math.radians(30.0))

# Lattice steps between neighbouring nodes, in tile widths / heights.
_LATERAL_STEP = 2
_SPINE_STEP = 2

# Blank lattice cells left between packed districts.
_DISTRICT_GAP_LATERAL = 1
_DISTRICT_GAP_SPINE = 1

# Width-to-height ratio the packed composition aims for, in screen pixels.
_TARGET_SCREEN_ASPECT = 1.45

# Blocks taller than this widen instead of growing further down, so a switch with
# many clients spreads sideways rather than becoming a narrow tower.
_MAX_BLOCK_ROWS = 6


@dataclass(frozen=True)
class _District:
    """A hub and its leaf children. Stays contiguous so its edges stay short."""

    hub: str | None
    members: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Shaped:
    """A district resolved to a concrete rectangle of lattice cells."""

    district: _District
    cols: int
    rows: int

    @property
    def width(self) -> int:
        return max(self.cols, 1)

    @property
    def height(self) -> int:
        # One row for the hub tile, then the block of members beneath it.
        return (1 if self.district.hub else 0) + self.rows


def _block_shape(count: int, max_cols: int) -> tuple[int, int]:
    """Choose (cols, rows) for a block of *count* tiles.

    A lateral step is wider on screen than a spine step, so a visually square
    block needs more rows than columns -- that is the ``natural`` width. Blocks
    that would exceed ``_MAX_BLOCK_ROWS`` widen instead, and nothing is allowed
    to grow past the shelf width.
    """
    if count <= 0:
        return 1, 0
    natural = max(1, round(math.sqrt(count * _TILE_ASPECT)))
    unstacked = math.ceil(count / _MAX_BLOCK_ROWS)
    cols = min(count, max_cols, max(natural, unstacked))
    return max(cols, 1), math.ceil(count / max(cols, 1))


def _partition_children(
    node: str,
    children: dict[str, list[str]],
) -> tuple[list[str], list[str]]:
    """Split a node's children into leaves (own district) and hubs (their own)."""
    leaves = [c for c in children.get(node, []) if not children.get(c)]
    hubs = [c for c in children.get(node, []) if children.get(c)]
    return leaves, hubs


def _take_district(
    node: str,
    children: dict[str, list[str]],
    placed: set[str],
) -> tuple[_District, list[str]]:
    """Claim *node* and its unplaced leaf children; return it and the hubs to visit."""
    placed.add(node)
    leaves, hubs = _partition_children(node, children)
    fresh = [leaf for leaf in leaves if leaf not in placed]
    placed.update(fresh)
    return _District(hub=node, members=tuple(fresh)), [h for h in hubs if h not in placed]


def _walk_districts(
    roots: list[str],
    children: dict[str, list[str]],
) -> tuple[list[_District], set[str]]:
    """Breadth-first walk building one district per hub, parents before children."""
    districts: list[_District] = []
    placed: set[str] = set()
    queue = list(roots)
    while queue:
        node = queue.pop(0)
        if node in placed:
            continue
        district, pending = _take_district(node, children, placed)
        districts.append(district)
        queue.extend(pending)
    return districts, placed


def _orphan_districts(nodes: set[str], placed: set[str], sort_key) -> list[_District]:
    """Nodes the walk never reached get parked in their own block."""
    stragglers = sorted(nodes - placed, key=sort_key)
    return [_District(hub=None, members=tuple(stragglers))] if stragglers else []


def _shape_all(districts: list[_District], max_cols: int) -> list[_Shaped]:
    shaped = []
    for district in districts:
        cols, rows = _block_shape(len(district.members), max_cols)
        shaped.append(_Shaped(district=district, cols=cols, rows=rows))
    return shaped


def _ideal_shelf_width(districts: list[_District]) -> int:
    """First guess at a shelf width, ignoring the gaps packing will introduce."""
    total = sum(len(d.members) + 1 for d in districts) or 1
    return max(1, int(round(math.sqrt(total * _TARGET_SCREEN_ASPECT * _TILE_ASPECT))))


@dataclass
class _ShelfState:
    target: int
    cursor_lat: int = 0
    shelf_spine: int = 0
    shelf_height: int = 0


def _advance_shelf(state: _ShelfState, shaped: _Shaped) -> tuple[int, int]:
    """Return the (lateral, spine) origin for *shaped*, wrapping when full."""
    if state.cursor_lat and state.cursor_lat + shaped.width > state.target:
        state.shelf_spine += state.shelf_height + _DISTRICT_GAP_SPINE
        state.cursor_lat = 0
        state.shelf_height = 0
    origin = (state.cursor_lat, state.shelf_spine)
    state.cursor_lat += shaped.width + _DISTRICT_GAP_LATERAL
    state.shelf_height = max(state.shelf_height, shaped.height)
    return origin


def _place_members(
    shaped: _Shaped,
    origin_lat: int,
    origin_spine: int,
) -> dict[str, tuple[int, int]]:
    """Lay the district's leaf members out row-major beneath the hub."""
    cells: dict[str, tuple[int, int]] = {}
    member_spine = origin_spine + (1 if shaped.district.hub else 0)
    for index, member in enumerate(shaped.district.members):
        cells[member] = (
            origin_lat + index % shaped.cols,
            member_spine + index // shaped.cols,
        )
    return cells


def _place_hub(
    shaped: _Shaped,
    origin_lat: int,
    origin_spine: int,
) -> dict[str, tuple[int, int]]:
    """Centre the hub tile over its block of members."""
    hub = shaped.district.hub
    if hub is None:
        return {}
    return {hub: (origin_lat + (shaped.width - 1) // 2, origin_spine)}


def _pack_at_width(districts: list[_District], target: int) -> dict[str, tuple[int, int]]:
    state = _ShelfState(target=target)
    cells: dict[str, tuple[int, int]] = {}
    for shaped in _shape_all(districts, target):
        origin_lat, origin_spine = _advance_shelf(state, shaped)
        cells.update(_place_hub(shaped, origin_lat, origin_spine))
        cells.update(_place_members(shaped, origin_lat, origin_spine))
    return cells


def _screen_aspect(cells: dict[str, tuple[int, int]]) -> float:
    """Width/height of the packed result in screen pixels, as a ratio."""
    lats = [lat for lat, _spine in cells.values()]
    spines = [spine for _lat, spine in cells.values()]
    width = max(lats) - min(lats) + 1
    height = max(spines) - min(spines) + 1
    return (width / height) / _TILE_ASPECT


def _aspect_error(cells: dict[str, tuple[int, int]]) -> float:
    """Log-ratio distance from the target aspect, so too-wide and too-tall rank alike."""
    return abs(math.log(_screen_aspect(cells) / _TARGET_SCREEN_ASPECT))


def _pack_districts(districts: list[_District]) -> dict[str, tuple[int, int]]:
    """Shelf-pack the districts, choosing the width whose result reads squarest.

    Shelf packing leaves ragged gaps, so the closed-form ideal width consistently
    overshoots. Trying the plausible widths and measuring is cheap and exact.
    """
    if not districts:
        return {}
    ideal = _ideal_shelf_width(districts)
    candidates = range(1, ideal * 3 + 2)
    packed = [_pack_at_width(districts, target) for target in candidates]
    return min(packed, key=_aspect_error)


def _to_iso_grid(cells: dict[str, tuple[int, int]]) -> dict[str, tuple[float, float]]:
    """Convert screen-aligned (lateral, spine) cells to isometric grid coordinates."""
    grid: dict[str, tuple[float, float]] = {}
    for name, (lat, spine) in cells.items():
        scaled_lat = lat * _LATERAL_STEP
        scaled_spine = spine * _SPINE_STEP
        grid[name] = (float(scaled_spine + scaled_lat), float(scaled_spine - scaled_lat))
    return grid


def _iso_district_grid(
    edges: list[Edge],
    node_types: dict[str, str],
) -> dict[str, tuple[float, float]]:
    """Assign every node a unique isometric grid cell using district packing."""
    nodes = _layout_nodeset(edges, node_types)
    children, incoming = _build_children_maps(edges, nodes)
    sort_key = _sort_key_for_nodes(node_types)
    _sort_children(children, sort_key)
    roots = _resolve_roots(nodes, incoming, node_types, sort_key)
    districts, placed = _walk_districts(roots, children)
    districts.extend(_orphan_districts(nodes, placed, sort_key))
    return _to_iso_grid(_pack_districts(districts))
