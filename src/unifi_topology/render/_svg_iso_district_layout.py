"""Compact 'district' layout for isometric diagrams.

The default tree layout assigns one axis to sibling order and the other to tree
depth. Real networks are shallow and wide, so that produces a long diagonal
strip: a 22x4 grid for 15 nodes, drawn as a thin line across a mostly empty
canvas. Averaging child indices also lets two parents land on the same cell,
which stacks nodes on top of each other.

This layout instead treats the ground plane as a plane. Each hub (a device with
children) and its leaf children form a *district*, and a hub's sub-districts are
placed directly beneath it, so a whole subtree occupies one contiguous
rectangle. That keeps every parent adjacent to its children: infrastructure
links stay short instead of stretching across the diagram.

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

# Blank lattice cells left between packed blocks.
_GAP_LATERAL = 1
_GAP_SPINE = 1

# Width-to-height ratio the packed composition aims for, in screen pixels.
_TARGET_SCREEN_ASPECT = 1.45

# Blocks taller than this widen instead of growing further down, so a switch with
# many clients spreads sideways rather than becoming a narrow tower.
_MAX_BLOCK_ROWS = 6


@dataclass(frozen=True)
class _Placed:
    """Nodes positioned in a (lateral, spine) rectangle with origin at (0, 0)."""

    cells: dict[str, tuple[int, int]]
    width: int
    height: int


_EMPTY = _Placed(cells={}, width=0, height=0)


def _shift(placed: _Placed, lateral: int, spine: int) -> _Placed:
    moved = {node: (lat + lateral, sp + spine) for node, (lat, sp) in placed.cells.items()}
    return _Placed(cells=moved, width=placed.width, height=placed.height)


def _centre(placed: _Placed, width: int) -> _Placed:
    return _shift(placed, (width - placed.width) // 2, 0)


def _block_shape(count: int, max_cols: int) -> tuple[int, int]:
    """Choose (cols, rows) for a block of *count* tiles.

    A lateral step is wider on screen than a spine step, so a visually square
    block needs more rows than columns -- that is the ``natural`` width. Blocks
    that would exceed ``_MAX_BLOCK_ROWS`` widen instead, and nothing is allowed
    to grow past the enclosing width.
    """
    if count <= 0:
        return 1, 0
    natural = max(1, round(math.sqrt(count * _TILE_ASPECT)))
    unstacked = math.ceil(count / _MAX_BLOCK_ROWS)
    cols = min(count, max_cols, max(natural, unstacked))
    return max(cols, 1), math.ceil(count / max(cols, 1))


def _leaf_block(members: list[str], max_cols: int) -> _Placed:
    """Lay leaf nodes out row-major in a compact rectangle."""
    if not members:
        return _EMPTY
    cols, rows = _block_shape(len(members), max_cols)
    cells = {node: (index % cols, index // cols) for index, node in enumerate(members)}
    return _Placed(cells=cells, width=cols, height=rows)


def _hub_over_block(hub: str, block: _Placed) -> _Placed:
    """Put the hub tile on its own row, centred above its leaf children."""
    width = max(block.width, 1)
    cells = {hub: ((width - 1) // 2, 0)}
    cells.update(_shift(_centre(block, width), 0, 1).cells)
    return _Placed(cells=cells, width=width, height=block.height + 1)


def _stack(top: _Placed, bottom: _Placed) -> _Placed:
    """Place *bottom* below *top*, each centred on the combined width."""
    if not bottom.cells:
        return top
    if not top.cells:
        return bottom
    width = max(top.width, bottom.width)
    cells = dict(_centre(top, width).cells)
    cells.update(_shift(_centre(bottom, width), 0, top.height + _GAP_SPINE).cells)
    return _Placed(cells=cells, width=width, height=top.height + _GAP_SPINE + bottom.height)


@dataclass
class _RowState:
    max_width: int
    lateral: int = 0
    spine: int = 0
    row_height: int = 0
    width: int = 0


def _row_origin(state: _RowState, block: _Placed) -> tuple[int, int]:
    """Origin for *block* on the current row, wrapping to a new one when full."""
    if state.lateral and state.lateral + block.width > state.max_width:
        state.spine += state.row_height + _GAP_SPINE
        state.lateral = 0
        state.row_height = 0
    origin = (state.lateral, state.spine)
    state.lateral += block.width + _GAP_LATERAL
    state.row_height = max(state.row_height, block.height)
    state.width = max(state.width, state.lateral - _GAP_LATERAL)
    return origin


def _pack_row(blocks: list[_Placed], max_width: int) -> _Placed:
    """Lay sibling blocks left to right, wrapping when they exceed *max_width*."""
    state = _RowState(max_width=max(max_width, 1))
    cells: dict[str, tuple[int, int]] = {}
    for block in blocks:
        lateral, spine = _row_origin(state, block)
        cells.update(_shift(block, lateral, spine).cells)
    return _Placed(cells=cells, width=state.width, height=state.spine + state.row_height)


def _claim_leaves(node: str, children: dict[str, list[str]], visited: set[str]) -> list[str]:
    leaves = [c for c in children.get(node, []) if not children.get(c) and c not in visited]
    visited.update(leaves)
    return leaves


def _place_children(
    node: str,
    children: dict[str, list[str]],
    visited: set[str],
    max_width: int,
) -> _Placed:
    """Place every sub-hub of *node* as its own subtree, side by side."""
    blocks: list[_Placed] = []
    for child in children.get(node, []):
        # Re-checked each pass: an earlier sibling's subtree may have claimed it.
        if child in visited or not children.get(child):
            continue
        blocks.append(_place_subtree(child, children, visited, max_width))
    return _pack_row(blocks, max_width)


def _place_subtree(
    node: str,
    children: dict[str, list[str]],
    visited: set[str],
    max_width: int,
) -> _Placed:
    """Place *node*, its leaf children, and every sub-hub beneath it."""
    visited.add(node)
    own = _hub_over_block(node, _leaf_block(_claim_leaves(node, children, visited), max_width))
    return _stack(own, _place_children(node, children, visited, max_width))


def _subtree_blocks(
    order: list[str],
    children: dict[str, list[str]],
    visited: set[str],
    max_width: int,
) -> list[_Placed]:
    blocks: list[_Placed] = []
    for node in order:
        if node in visited or not children.get(node):
            continue
        blocks.append(_place_subtree(node, children, visited, max_width))
    return blocks


def _ideal_width(node_count: int) -> int:
    """First guess at an enclosing width, ignoring gaps and ragged rows."""
    total = max(node_count, 1)
    return max(1, int(round(math.sqrt(total * _TARGET_SCREEN_ASPECT * _TILE_ASPECT))))


def _place_forest(
    roots: list[str],
    children: dict[str, list[str]],
    nodes: set[str],
    max_width: int,
    sort_key,
) -> _Placed:
    """Place every subtree, then park whatever the walk never reached."""
    visited: set[str] = set()
    order = list(roots) + sorted(nodes, key=sort_key)
    blocks = _subtree_blocks(order, children, visited, max_width)
    orphans = sorted(nodes - visited, key=sort_key)
    if orphans:
        blocks.append(_leaf_block(orphans, max_width))
    return _pack_row(blocks, max_width)


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


def _aspect_error(placed: _Placed) -> float:
    """Log-ratio distance from the target aspect, so too-wide and too-tall rank alike."""
    if not placed.cells:
        return 0.0
    return abs(math.log(_screen_aspect(placed.cells) / _TARGET_SCREEN_ASPECT))


def _best_placement(
    roots: list[str],
    children: dict[str, list[str]],
    nodes: set[str],
    sort_key,
) -> _Placed:
    """Try every plausible enclosing width and keep the squarest result.

    Wrapping leaves ragged gaps that no closed-form width can predict, so the
    layout is run at each candidate and measured.
    """
    ideal = _ideal_width(len(nodes))
    candidates = range(1, ideal * 3 + 2)
    placements = [_place_forest(roots, children, nodes, w, sort_key) for w in candidates]
    return min(placements, key=_aspect_error)


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
