"""Group-aware grid placement for isometric diagrams.

The tree and district layouts place nodes by topology alone. Drawing a group as
the bounding parallelogram of its members then makes groups overlap and enclose
non-members. Here every group is laid out on its own and the blocks are set side
by side along the grid x axis, so each boundary holds exactly its members.
"""

from __future__ import annotations

from collections.abc import Callable

from ..model.topology import Edge
from ._svg_group_layout import (
    _build_node_to_group_map,
    _filter_edges_for_group,
    _resolve_group_order,
)
from ._svg_tree_layout import _layout_nodeset

GridPositions = dict[str, tuple[float, float]]
PlaceFn = Callable[[list[Edge], dict[str, str]], GridPositions]


def _group_blocks(
    nodes: set[str],
    groups: dict[str, list[str]],
    group_order: list[str] | None,
) -> list[set[str]]:
    """Return each group's laid-out members in order, then any remaining nodes."""
    members: dict[str, set[str]] = {}
    for node, group_name in _build_node_to_group_map(groups).items():
        members.setdefault(group_name, set()).add(node)
    blocks = [
        members.get(group_name, set()) & nodes
        for group_name in _resolve_group_order(groups, group_order)
    ]
    blocks.append(nodes.difference(*blocks))
    return [block for block in blocks if block]


def _shifted_block(grid: GridPositions, start_gx: float) -> GridPositions:
    """Move a block so it starts at *start_gx* on the x axis and 0 on the y axis."""
    min_gx = min(gx for gx, _ in grid.values())
    min_gy = min(gy for _, gy in grid.values())
    return {name: (gx - min_gx + start_gx, gy - min_gy) for name, (gx, gy) in grid.items()}


def iso_grouped_grid(
    edges: list[Edge],
    node_types: dict[str, str],
    groups: dict[str, list[str]],
    group_order: list[str] | None,
    *,
    place: PlaceFn,
    gap: float,
) -> GridPositions:
    """Lay out each group with *place* and set the blocks *gap* cells apart."""
    result: GridPositions = {}
    start_gx = 0.0
    for block in _group_blocks(_layout_nodeset(edges, node_types), groups, group_order):
        block_types = {name: node_types.get(name, "other") for name in block}
        placed = _shifted_block(place(_filter_edges_for_group(edges, block), block_types), start_gx)
        result.update(placed)
        start_gx = max(gx for gx, _ in placed.values()) + gap
    return result
