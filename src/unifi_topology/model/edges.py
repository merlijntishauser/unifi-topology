"""Edge building and topology construction."""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Iterable

from . import _edge_discovery
from .classify import classify_device_type
from .topology import (
    Device,
    Edge,
    PortMap,
    TopologyResult,
)
from .topology import (
    build_device_index as _build_device_index,
)

logger = logging.getLogger(__name__)

build_device_index = _build_device_index
_lldp_candidates = _edge_discovery._lldp_candidates
_match_port_by_name = _edge_discovery._match_port_by_name
_match_port_by_number = _edge_discovery._match_port_by_number
_resolve_port_idx_from_lldp = _edge_discovery._resolve_port_idx_from_lldp
_find_port_by_idx = _edge_discovery._find_port_by_idx
_port_speed_by_idx = _edge_discovery._port_speed_by_idx
_port_vlans_by_idx = _edge_discovery._port_vlans_by_idx
_populate_port_maps = _edge_discovery._populate_port_maps
_collect_lldp_links = _edge_discovery._collect_lldp_links
_uplink_name = _edge_discovery._uplink_name
_maybe_add_uplink_link = _edge_discovery._maybe_add_uplink_link
_collect_uplink_links = _edge_discovery._collect_uplink_links
_build_ordered_edges = _edge_discovery._build_ordered_edges


def _discover_links(
    devices: Iterable[Device],
    *,
    include_ports: bool,
    only_unifi: bool,
) -> tuple[_edge_discovery.EdgeInputs, _edge_discovery.EdgeDiscoveryResult]:
    inputs = _edge_discovery.prepare_edge_inputs(devices)
    discovery = _edge_discovery.discover_edge_links(
        inputs,
        include_ports=include_ports,
        only_unifi=only_unifi,
    )
    return inputs, discovery


def build_edges(
    devices: Iterable[Device],
    *,
    include_ports: bool = False,
    only_unifi: bool = True,
) -> list[Edge]:
    """Build edges between devices from LLDP and uplink data."""
    inputs, discovery = _discover_links(
        devices,
        include_ports=include_ports,
        only_unifi=only_unifi,
    )
    edges = _build_ordered_edges(
        discovery.raw_links,
        discovery.port_map,
        discovery.poe_map,
        discovery.speed_map,
        discovery.vlan_map,
        inputs.device_by_name,
        include_ports=include_ports,
    )

    poe_edges = sum(1 for edge in edges if edge.poe)
    logger.debug("Built %d unique edges (%d PoE)", len(edges), poe_edges)
    return edges


def build_port_map(devices: Iterable[Device], *, only_unifi: bool = True) -> PortMap:
    """Build port label map from device data."""
    _, discovery = _discover_links(
        devices,
        include_ports=True,
        only_unifi=only_unifi,
    )
    return discovery.port_map


def _build_adjacency(edges: Iterable[Edge]) -> dict[str, set[str]]:
    """Build adjacency list from edges."""
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        adjacency.setdefault(edge.left, set()).add(edge.right)
        adjacency.setdefault(edge.right, set()).add(edge.left)
    return adjacency


def _build_edge_map(edges: Iterable[Edge]) -> dict[frozenset[str], Edge]:
    """Build edge lookup map."""
    return {frozenset({edge.left, edge.right}): edge for edge in edges}


def _tree_parents(adjacency: dict[str, set[str]], gateways: list[str]) -> dict[str, str]:
    """BFS to find parent for each node in tree."""
    visited: set[str] = set()
    parent: dict[str, str] = {}
    queue: deque[str] = deque()

    for gateway in gateways:
        if gateway in adjacency:
            visited.add(gateway)
            queue.append(gateway)

    while queue:
        current = queue.popleft()
        for neighbor in sorted(adjacency.get(current, set())):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            parent[neighbor] = current
            queue.append(neighbor)
    return parent


def _tree_edges_from_parent(
    parent: dict[str, str], edge_map: dict[frozenset[str], Edge]
) -> list[Edge]:
    """Build tree edges from parent map."""
    tree_edges: list[Edge] = []
    for child in sorted(parent):
        parent_name = parent[child]
        original = edge_map.get(frozenset({child, parent_name}))
        if original is None:
            tree_edges.append(Edge(left=parent_name, right=child))
        else:
            tree_edges.append(
                Edge(
                    left=parent_name,
                    right=child,
                    label=original.label,
                    poe=original.poe,
                    wireless=original.wireless,
                    speed=original.speed,
                    channel=original.channel,
                    vlans=original.vlans,
                    active_vlans=original.active_vlans,
                    is_trunk=original.is_trunk,
                )
            )
    return tree_edges


def build_tree_edges_by_topology(edges: Iterable[Edge], gateways: list[str]) -> list[Edge]:
    """Build tree edges rooted at gateways using BFS."""
    if not gateways:
        return []
    adjacency = _build_adjacency(edges)
    edge_map = _build_edge_map(edges)
    parent = _tree_parents(adjacency, gateways)
    return _tree_edges_from_parent(parent, edge_map)


def enrich_edges_with_active_vlans(
    edges: list[Edge],
    client_edges: list[Edge],
) -> list[Edge]:
    """Add active_vlans to edges based on client traffic."""
    device_active_vlans: dict[str, set[int]] = {}
    for client_edge in client_edges:
        device_name = client_edge.left
        for vlan in client_edge.active_vlans:
            device_active_vlans.setdefault(device_name, set()).add(vlan)

    enriched: list[Edge] = []
    for edge in edges:
        left_active = device_active_vlans.get(edge.left, set())
        right_active = device_active_vlans.get(edge.right, set())
        combined_active = left_active | right_active
        active_vlans = tuple(sorted(set(edge.vlans) & combined_active))
        enriched.append(
            Edge(
                left=edge.left,
                right=edge.right,
                label=edge.label,
                poe=edge.poe,
                wireless=edge.wireless,
                speed=edge.speed,
                channel=edge.channel,
                vlans=edge.vlans,
                active_vlans=active_vlans,
                is_trunk=edge.is_trunk,
            )
        )
    return enriched


def build_topology(
    devices: Iterable[Device],
    *,
    include_ports: bool,
    only_unifi: bool,
    gateways: list[str],
) -> TopologyResult:
    """Build complete topology from devices."""
    normalized_devices = list(devices)
    lldp_entries = sum(len(device.lldp_info) for device in normalized_devices)
    logger.debug(
        "Normalized %d devices (%d LLDP entries)",
        len(normalized_devices),
        lldp_entries,
    )
    raw_edges = build_edges(normalized_devices, include_ports=include_ports, only_unifi=only_unifi)
    tree_edges = build_tree_edges_by_topology(raw_edges, gateways)
    logger.debug(
        "Built %d hierarchy edges (gateways=%d)",
        len(tree_edges),
        len(gateways),
    )
    return TopologyResult(raw_edges=raw_edges, tree_edges=tree_edges)


def group_devices_by_type(devices: Iterable[Device]) -> dict[str, list[str]]:
    """Group devices by their type."""
    groups: dict[str, list[str]] = {"gateway": [], "switch": [], "ap": [], "other": []}
    for device in devices:
        group = classify_device_type(device)
        groups[group].append(device.name)
    return groups


def _primary_vlan_for_node(
    node: str,
    edges: list[Edge],
) -> int | None:
    """Find the primary VLAN for a node from its edges.

    Uses active_vlans first, falls back to vlans, picks lowest VLAN ID.
    """
    vlans: set[int] = set()
    for edge in edges:
        if edge.left != node and edge.right != node:
            continue
        if edge.active_vlans:
            vlans.update(edge.active_vlans)
        elif edge.vlans:
            vlans.update(edge.vlans)
    return min(vlans) if vlans else None


def group_nodes_by_vlan(
    edges: list[Edge],
    vlan_names: dict[int, str] | None = None,
) -> tuple[dict[str, list[str]], list[str], dict[str, int]]:
    """Group nodes by their primary VLAN membership.

    Returns (groups, group_order, group_vlan_ids) where groups maps VLAN name
    to node list, group_order sorts by VLAN ID ascending with "Unassigned" last,
    and group_vlan_ids maps group name to its VLAN ID.
    """
    vlan_names = vlan_names or {}
    nodes: set[str] = set()
    for edge in edges:
        nodes.add(edge.left)
        nodes.add(edge.right)

    vlan_groups: dict[int, list[str]] = {}
    unassigned: list[str] = []

    for node in sorted(nodes):
        vlan_id = _primary_vlan_for_node(node, edges)
        if vlan_id is None:
            unassigned.append(node)
        else:
            vlan_groups.setdefault(vlan_id, []).append(node)

    groups: dict[str, list[str]] = {}
    group_vlan_ids: dict[str, int] = {}
    group_order: list[str] = []

    for vlan_id in sorted(vlan_groups):
        name = vlan_names.get(vlan_id, f"VLAN {vlan_id}")
        groups[name] = vlan_groups[vlan_id]
        group_vlan_ids[name] = vlan_id
        group_order.append(name)

    if unassigned:
        groups["Unassigned"] = unassigned
        group_order.append("Unassigned")

    return groups, group_order, group_vlan_ids
