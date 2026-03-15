"""Private helpers for grouped SVG layouts and node group attributes."""

from __future__ import annotations

from dataclasses import dataclass

from ..model.topology import Edge
from ._svg_node_attrs import _svg_node_group_attrs as _svg_node_group_attrs
from ._svg_tree_layout import _layout_nodes, _layout_nodeset
from .svg_theme import SvgOptions


@dataclass(frozen=True)
class GroupBounds:
    name: str
    x: float
    y: float
    width: float
    height: float


def _assign_nodes_to_groups(
    nodes: set[str],
    groups: dict[str, list[str]],
) -> dict[str, str]:
    """Map each node to its group name."""
    node_to_group: dict[str, str] = {}
    for group_name, members in groups.items():
        for node in members:
            if node in nodes:
                node_to_group[node] = group_name
    return node_to_group


def _resolve_group_order(
    groups: dict[str, list[str]],
    group_order: list[str] | None,
) -> list[str]:
    """Return ordered list of group names."""
    if group_order:
        return [group_name for group_name in group_order if group_name in groups]
    return sorted(groups.keys())


def _filter_edges_for_group(
    edges: list[Edge],
    group_nodes: set[str],
) -> list[Edge]:
    """Return edges where both endpoints are in the group."""
    return [edge for edge in edges if edge.left in group_nodes and edge.right in group_nodes]


def _layout_single_group(
    edges: list[Edge],
    group_nodes: set[str],
    node_types: dict[str, str],
    options: SvgOptions,
) -> tuple[dict[str, tuple[float, float]], float, float]:
    """Layout nodes within a single group, return positions and dimensions."""
    group_edges = _filter_edges_for_group(edges, group_nodes)
    group_node_types = {name: node_types.get(name, "other") for name in group_nodes}
    positions, width, height = _layout_nodes(group_edges, group_node_types, options)
    return positions, float(width), float(height)


def _compute_group_bounds(
    group_name: str,
    positions: dict[str, tuple[float, float]],
    options: SvgOptions,
    offset_x: float,
) -> GroupBounds:
    """Compute bounding rectangle for a group."""
    if not positions:
        return GroupBounds(group_name, offset_x, 0, 100, 100)
    xs = [x for x, _ in positions.values()]
    ys = [y for _, y in positions.values()]
    min_x = min(xs) - options.group_padding
    min_y = min(ys) - options.group_padding
    max_x = max(xs) + options.node_width + options.group_padding
    max_y = max(ys) + options.node_height + options.group_padding
    return GroupBounds(group_name, min_x, min_y, max_x - min_x, max_y - min_y)


def _offset_positions(
    positions: dict[str, tuple[float, float]],
    dx: float,
    dy: float,
) -> dict[str, tuple[float, float]]:
    """Shift all positions by (dx, dy)."""
    return {name: (x + dx, y + dy) for name, (x, y) in positions.items()}


def _layout_ungrouped_nodes(
    edges: list[Edge],
    node_types: dict[str, str],
    options: SvgOptions,
    all_nodes: set[str],
    node_to_group: dict[str, str],
    current_x: float,
) -> tuple[dict[str, tuple[float, float]], GroupBounds | None, float, float]:
    ungrouped = all_nodes - set(node_to_group.keys())
    if not ungrouped:
        return {}, None, current_x, 0.0
    positions, width, height = _layout_single_group(edges, ungrouped, node_types, options)
    offset_positions = _offset_positions(positions, current_x - options.padding, 0)
    bounds = _compute_group_bounds("Other", offset_positions, options, current_x)
    next_x = current_x + width + options.group_gap
    return offset_positions, bounds, next_x, height


def _layout_grouped_nodes(
    edges: list[Edge],
    node_types: dict[str, str],
    options: SvgOptions,
    groups: dict[str, list[str]],
    group_order: list[str] | None,
) -> tuple[dict[str, tuple[float, float]], list[GroupBounds], int, int]:
    """Layout nodes in horizontal group lanes."""
    all_nodes = _layout_nodeset(edges, node_types)
    ordered_groups = _resolve_group_order(groups, group_order)
    node_to_group = _assign_nodes_to_groups(all_nodes, groups)

    all_positions: dict[str, tuple[float, float]] = {}
    group_bounds_list: list[GroupBounds] = []
    current_x = float(options.padding)
    max_height = 0.0

    for group_name in ordered_groups:
        group_nodes = set(groups.get(group_name, [])) & all_nodes
        if not group_nodes:
            continue
        positions, width, height = _layout_single_group(edges, group_nodes, node_types, options)
        offset_positions = _offset_positions(positions, current_x - options.padding, 0)
        all_positions.update(offset_positions)
        group_bounds_list.append(_compute_group_bounds(group_name, offset_positions, options, current_x))
        current_x += width + options.group_gap
        max_height = max(max_height, height)

    ungrouped_positions, ungrouped_bounds, current_x, ungrouped_height = _layout_ungrouped_nodes(
        edges,
        node_types,
        options,
        all_nodes,
        node_to_group,
        current_x,
    )
    all_positions.update(ungrouped_positions)
    if ungrouped_bounds is not None:
        group_bounds_list.append(ungrouped_bounds)
    max_height = max(max_height, ungrouped_height)

    total_width = int(current_x - options.group_gap + options.padding)
    total_height = int(max_height)
    return all_positions, group_bounds_list, total_width, total_height


def _build_node_to_group_map(groups: dict[str, list[str]]) -> dict[str, str]:
    """Build reverse mapping from node to group name."""
    result: dict[str, str] = {}
    for group_name, members in groups.items():
        for node in members:
            result[node] = group_name
    return result
