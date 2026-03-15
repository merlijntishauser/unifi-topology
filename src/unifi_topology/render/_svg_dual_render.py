"""Private helpers for dual physical/VLAN SVG rendering."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass

from ..model.topology import Edge, VpnTunnel, WanInfo
from .svg_theme import SvgOptions, SvgTheme


@dataclass(frozen=True)
class DualRenderGroups:
    groups: dict[str, list[str]]
    group_order: list[str]
    group_vlan_ids: dict[str, int]


def _partition_vlan_nodes(
    vlan_node_map: dict[str, int | None],
) -> tuple[dict[int, list[str]], list[str]]:
    vlan_groups: dict[int, list[str]] = {}
    unassigned: list[str] = []
    for node in sorted(vlan_node_map):
        vlan_id = vlan_node_map[node]
        if vlan_id is None:
            unassigned.append(node)
            continue
        vlan_groups.setdefault(vlan_id, []).append(node)
    return vlan_groups, unassigned


def _named_vlan_groups(
    vlan_groups: dict[int, list[str]],
    vlan_names: dict[int, str],
) -> DualRenderGroups:
    groups: dict[str, list[str]] = {}
    group_vlan_ids: dict[str, int] = {}
    group_order: list[str] = []
    for vlan_id in sorted(vlan_groups):
        name = vlan_names.get(vlan_id, f"VLAN {vlan_id}")
        groups[name] = vlan_groups[vlan_id]
        group_vlan_ids[name] = vlan_id
        group_order.append(name)
    return DualRenderGroups(
        groups=groups,
        group_order=group_order,
        group_vlan_ids=group_vlan_ids,
    )


def _with_unassigned_group(
    dual_groups: DualRenderGroups,
    unassigned: list[str],
) -> DualRenderGroups:
    if not unassigned:
        return dual_groups
    groups = dict(dual_groups.groups)
    group_order = list(dual_groups.group_order)
    groups["Unassigned"] = unassigned
    group_order.append("Unassigned")
    return DualRenderGroups(
        groups=groups,
        group_order=group_order,
        group_vlan_ids=dual_groups.group_vlan_ids,
    )


def _groups_from_vlan_node_map(
    vlan_node_map: dict[str, int | None],
    vlan_names: dict[int, str] | None = None,
) -> DualRenderGroups:
    """Convert a node-to-VLAN mapping into group structures."""
    vlan_groups, unassigned = _partition_vlan_nodes(vlan_node_map)
    dual_groups = _named_vlan_groups(vlan_groups, vlan_names or {})
    return _with_unassigned_group(dual_groups, unassigned)


def resolve_dual_groups(
    *,
    edges: list[Edge],
    vlan_names: dict[int, str] | None,
    vlan_node_map: dict[str, int | None] | None,
    group_nodes_by_vlan: Callable[
        [list[Edge], dict[int, str]],
        tuple[dict[str, list[str]], list[str], dict[str, int]],
    ],
) -> DualRenderGroups | None:
    if vlan_node_map:
        return _groups_from_vlan_node_map(vlan_node_map, vlan_names)
    if not vlan_names:
        return None
    groups, group_order, group_vlan_ids = group_nodes_by_vlan(edges, vlan_names)
    if not groups:
        return None
    return DualRenderGroups(
        groups=groups,
        group_order=group_order,
        group_vlan_ids=group_vlan_ids,
    )


def render_dual_svgs(
    edges: list[Edge],
    *,
    node_types: dict[str, str],
    options: SvgOptions,
    theme: SvgTheme,
    wan_info: WanInfo | None,
    vpn_tunnels: list[VpnTunnel] | None,
    dual_groups: DualRenderGroups | None,
    render_fn: Callable[..., str],
) -> dict[str, str | None]:
    physical_svg = render_fn(
        edges,
        node_types=node_types,
        options=dataclasses.replace(options, layout_mode="physical"),
        theme=theme,
        wan_info=wan_info,
        vpn_tunnels=vpn_tunnels,
    )
    if dual_groups is None:
        return {"physical": physical_svg, "vlan": None}

    vlan_svg = render_fn(
        edges,
        node_types=node_types,
        options=dataclasses.replace(options, layout_mode="grouped"),
        theme=theme,
        groups=dual_groups.groups,
        group_order=dual_groups.group_order,
        group_vlan_ids=dual_groups.group_vlan_ids,
        wan_info=wan_info,
        vpn_tunnels=vpn_tunnels,
    )
    return {"physical": physical_svg, "vlan": vlan_svg}
