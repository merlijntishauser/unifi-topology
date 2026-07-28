"""Compact 'district' layout for isometric diagrams.

The default tree layout assigns one axis to sibling order and the other to tree
depth. Real networks are shallow and wide, so that produces a long diagonal
strip: a 22x4 grid for 15 nodes, drawn as a thin line across a mostly empty
canvas. Averaging child indices also lets two parents land on the same cell,
which stacks nodes on top of each other.

This layout treats the ground plane as a plane, with one grammar per subtree:
the hub's child hubs sit directly below it, so the infrastructure trunk runs
unbroken down the left of each subtree, and the hub's own leaf clients form a
block immediately to its right. An earlier version put the leaf block between
hub and children, which pushed connected infrastructure four to seven cells
apart and left most of the bounding box empty.

Placement is searched, not computed: candidate wrap widths and leaf-block widen
factors are each laid out in full, then scored by distance from the target
screen aspect with density breaking ties. Without the widen factors the search
is a no-op for narrow trees -- a chain renders one cell wide no matter what
width it is offered.

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
    _sort_key_for_nodes,
)

# Screen height of one spine step divided by screen width of one lateral step.
# Equal to tan(30 degrees) for a true isometric projection.
_TILE_ASPECT = math.tan(math.radians(30.0))

# Lattice steps between neighbouring nodes, in tile widths / heights.
_LATERAL_STEP = 2
_SPINE_STEP = 2

# Blank lattice cells left between sibling blocks on a row.
_GAP_LATERAL = 1

# Width-to-height ratio the packed composition aims for, in screen pixels.
_TARGET_SCREEN_ASPECT = 1.45

# Leaf-block widen factors tried by the placement search. Narrow trees cannot
# reach the target aspect by wrapping alone; widening their leaf fields can.
_WIDEN_FACTORS = (1.0, 1.5, 2.0)

# Blocks taller than this widen instead of growing further down, so a switch
# with many clients spreads sideways rather than becoming a narrow tower.
_MAX_BLOCK_ROWS = 6


@dataclass(frozen=True)
class _Placed:
    """Nodes positioned in a (lateral, spine) rectangle with origin at (0, 0)."""

    cells: dict[str, tuple[int, int]]
    width: int
    height: int


@dataclass(frozen=True)
class _PackSpec:
    """One candidate of the placement search: wrap width and leaf widen factor."""

    width: int
    widen: float


_EMPTY = _Placed(cells={}, width=0, height=0)


def _shift(placed: _Placed, lateral: int, spine: int) -> dict[str, tuple[int, int]]:
    return {node: (lat + lateral, sp + spine) for node, (lat, sp) in placed.cells.items()}


def _block_shape(count: int, spec: _PackSpec) -> tuple[int, int]:
    """Choose (cols, rows) for a leaf block.

    A lateral step is wider on screen than a spine step, so a visually square
    block needs more rows than columns -- that is the ``natural`` width, which
    the search's widen factor scales. Blocks that would exceed
    ``_MAX_BLOCK_ROWS`` widen regardless, and nothing grows past the wrap width.
    """
    if count <= 0:
        return 1, 0
    natural = max(1, round(math.sqrt(count * _TILE_ASPECT) * spec.widen))
    unstacked = math.ceil(count / _MAX_BLOCK_ROWS)
    cols = min(count, max(spec.width, 1), max(natural, unstacked))
    return max(cols, 1), math.ceil(count / max(cols, 1))


def _leaf_block(members: list[str], spec: _PackSpec) -> _Placed:
    """Lay leaf nodes out row-major in a compact rectangle."""
    if not members:
        return _EMPTY
    cols, rows = _block_shape(len(members), spec)
    cells = {node: (index % cols, index // cols) for index, node in enumerate(members)}
    return _Placed(cells=cells, width=cols, height=rows)


def _bare_hub(hub: str) -> _Placed:
    return _Placed(cells={hub: (0, 0)}, width=1, height=1)


def _stack_left(top: _Placed, bottom: _Placed) -> _Placed:
    """Place *bottom* directly below *top*, both flush left.

    No gap and no centring: this joins a hub to its child hubs, and the trunk
    they form should be straight and adjacent.
    """
    if not bottom.cells:
        return top
    cells = dict(top.cells)
    cells.update(_shift(bottom, 0, top.height))
    return _Placed(
        cells=cells, width=max(top.width, bottom.width), height=top.height + bottom.height
    )


def _beside(left: _Placed, right: _Placed) -> _Placed:
    """Place *right* immediately to the right of *left*, both flush top."""
    if not right.cells:
        return left
    cells = dict(left.cells)
    cells.update(_shift(right, left.width, 0))
    return _Placed(
        cells=cells, width=left.width + right.width, height=max(left.height, right.height)
    )


def _plan_rows(blocks: list[_Placed], width: int) -> list[list[tuple[_Placed, int]]]:
    """Assign blocks to wrap rows, greedily, returning (block, lateral) per row."""
    rows: list[list[tuple[_Placed, int]]] = [[]]
    lateral = 0
    for block in blocks:
        if lateral and lateral + block.width > max(width, 1):
            rows.append([])
            lateral = 0
        rows[-1].append((block, lateral))
        lateral += block.width + _GAP_LATERAL
    return rows


def _emit_row(
    cells: dict[str, tuple[int, int]],
    row: list[tuple[_Placed, int]],
    spine: int,
    *,
    centre: bool,
) -> tuple[int, int]:
    """Write one row's blocks into *cells*; return (row height, row width)."""
    height = max((block.height for block, _lat in row), default=0)
    width = 0
    for block, lateral in row:
        drop = (height - block.height) // 2 if centre else 0
        cells.update(_shift(block, lateral, spine + drop))
        width = max(width, lateral + block.width)
    return height, width


def _pack_row(blocks: list[_Placed], width: int, *, centre: bool = False) -> _Placed:
    """Lay blocks left to right, wrapping at *width*.

    Child rows stay flush top so every hub is adjacent to the parent above it;
    the forest row centres instead, so a short orphan block sits balanced beside
    a tall tree rather than pinned to its top corner.
    """
    cells: dict[str, tuple[int, int]] = {}
    spine = 0
    total_width = 0
    for row in _plan_rows(blocks, width):
        height, row_width = _emit_row(cells, row, spine, centre=centre)
        spine += height
        total_width = max(total_width, row_width)
    return _Placed(cells=cells, width=total_width, height=spine)


def _claim_leaves(node: str, children: dict[str, list[str]], visited: set[str]) -> list[str]:
    leaves = [c for c in children.get(node, []) if not children.get(c) and c not in visited]
    visited.update(leaves)
    return leaves


def _place_children(
    node: str,
    children: dict[str, list[str]],
    visited: set[str],
    spec: _PackSpec,
) -> _Placed:
    """Place every sub-hub of *node* as its own subtree, side by side."""
    blocks: list[_Placed] = []
    for child in children.get(node, []):
        # Re-checked each pass: an earlier sibling's subtree may have claimed it.
        if child in visited or not children.get(child):
            continue
        blocks.append(_place_subtree(child, children, visited, spec))
    return _pack_row(blocks, spec.width)


def _place_subtree(
    node: str,
    children: dict[str, list[str]],
    visited: set[str],
    spec: _PackSpec,
) -> _Placed:
    """Place *node* with its child hubs below and its leaf clients beside it."""
    visited.add(node)
    leaves = _claim_leaves(node, children, visited)
    trunk = _stack_left(_bare_hub(node), _place_children(node, children, visited, spec))
    return _beside(trunk, _leaf_block(leaves, spec))


def _subtree_blocks(
    order: list[str],
    children: dict[str, list[str]],
    visited: set[str],
    spec: _PackSpec,
) -> list[_Placed]:
    blocks: list[_Placed] = []
    for node in order:
        if node in visited or not children.get(node):
            continue
        blocks.append(_place_subtree(node, children, visited, spec))
    return blocks


def _ideal_width(node_count: int) -> int:
    """First guess at a wrap width, ignoring gaps and ragged rows."""
    total = max(node_count, 1)
    return max(1, int(round(math.sqrt(total * _TARGET_SCREEN_ASPECT * _TILE_ASPECT))))


def _place_forest(
    roots: list[str],
    children: dict[str, list[str]],
    nodes: set[str],
    spec: _PackSpec,
    sort_key,
) -> _Placed:
    """Place every subtree, then park whatever the walk never reached."""
    visited: set[str] = set()
    order = list(roots) + sorted(nodes, key=sort_key)
    blocks = _subtree_blocks(order, children, visited, spec)
    orphans = sorted(nodes - visited, key=sort_key)
    if orphans:
        blocks.append(_leaf_block(orphans, spec))
    return _pack_row(blocks, spec.width, centre=True)


def _adjacency(edges: list[Edge], nodes: set[str]) -> dict[str, list[str]]:
    """Undirected neighbour map."""
    adj: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in edges:
        adj[edge.left].append(edge.right)
        adj[edge.right].append(edge.left)
    return adj


def _grow_tree(
    adj: dict[str, list[str]],
    start: str,
    seen: set[str],
    children: dict[str, list[str]],
    sort_key,
) -> None:
    """Breadth-first expansion from *start*, recording the tree it spans."""
    seen.add(start)
    queue = [start]
    while queue:
        node = queue.pop(0)
        for neighbour in sorted(adj.get(node, []), key=sort_key):
            if neighbour in seen:
                continue
            seen.add(neighbour)
            children[node].append(neighbour)
            queue.append(neighbour)


def _spanning_children(
    adj: dict[str, list[str]],
    roots: list[str],
    sort_key,
) -> dict[str, list[str]]:
    """Build a placement tree from connectivity rather than edge direction.

    LLDP reports a link from whichever end saw it, so following ``left -> right``
    alone leaves part of the infrastructure unrooted. On a live 10-device network
    four switches and access points ended up outside the gateway's tree and were
    packed as separate top-level blocks, stretching the links back to them across
    the whole diagram.
    """
    children: dict[str, list[str]] = {node: [] for node in adj}
    seen: set[str] = set()
    for start in list(roots) + sorted(adj, key=sort_key):
        if start not in seen:
            _grow_tree(adj, start, seen, children, sort_key)
    return children


def _screen_aspect(cells: dict[str, tuple[int, int]]) -> float:
    """Width/height of the packed result in screen pixels, as a ratio."""
    lats = [lat for lat, _spine in cells.values()]
    spines = [spine for _lat, spine in cells.values()]
    width = max(lats) - min(lats) + 1
    height = max(spines) - min(spines) + 1
    return (width / height) / _TILE_ASPECT


def _fill(cells: dict[str, tuple[int, int]]) -> float:
    """Fraction of the content bounding box that holds a node."""
    lats = [lat for lat, _spine in cells.values()]
    spines = [spine for _lat, spine in cells.values()]
    area = (max(lats) - min(lats) + 1) * (max(spines) - min(spines) + 1)
    return len(cells) / area


def _placement_score(placed: _Placed) -> tuple[int, float]:
    """Near the target aspect first, then as dense as possible.

    Aspect error is bucketed so that candidates in the same neighbourhood
    compete on density instead of on meaningless third-decimal aspect wins --
    density is what stops the search wrapping a composition full of holes.
    """
    if not placed.cells:
        return (0, 0.0)
    error = abs(math.log(_screen_aspect(placed.cells) / _TARGET_SCREEN_ASPECT))
    return (int(error * 8), -_fill(placed.cells))


def _best_placement(
    roots: list[str],
    children: dict[str, list[str]],
    nodes: set[str],
    sort_key,
) -> _Placed:
    """Lay the forest out at every plausible width and widen factor; keep the best.

    Wrapping leaves ragged rows no closed form can predict, and narrow trees
    only reach the target aspect when their leaf blocks widen, so both axes of
    the search are laid out in full and measured.
    """
    ideal = _ideal_width(len(nodes))
    candidates = [
        _place_forest(roots, children, nodes, _PackSpec(width, widen), sort_key)
        for width in range(1, ideal * 3 + 2)
        for widen in _WIDEN_FACTORS
    ]
    return min(candidates, key=_placement_score)


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
    """Assign every node a unique isometric grid cell using subtree packing."""
    nodes = _layout_nodeset(edges, node_types)
    _directed, incoming = _build_children_maps(edges, nodes)
    sort_key = _sort_key_for_nodes(node_types)
    roots = _resolve_roots(nodes, incoming, node_types, sort_key)
    children = _spanning_children(_adjacency(edges, nodes), roots, sort_key)
    return _to_iso_grid(_best_placement(roots, children, nodes, sort_key).cells)
