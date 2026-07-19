"""Client handling and edge building."""

from __future__ import annotations

from collections.abc import Iterable
from typing import NamedTuple

from . import _client_access
from .classify import (
    classify_client_type,
    classify_device_type,
    client_is_unifi,
)
from .helpers import normalize_mac
from .topology import ClientPortMap, Device, Edge

_client_channel = _client_access._client_channel
_client_is_wired = _client_access._client_is_wired
_client_vlan = _client_access._client_vlan
_extract_connection_info = _client_access._extract_connection_info
client_node_id = _client_access.client_node_id
client_uplink_mac = _client_access.client_uplink_mac
client_uplink_port = _client_access.client_uplink_port


def _client_matches_mode(client: object, mode: str) -> bool:
    """Check if client matches wired/wireless mode filter."""
    wired = _client_is_wired(client)
    if mode == "all":
        return True
    if mode == "wireless":
        return not wired
    return wired


def client_matches_filters(client: object, *, client_mode: str, only_unifi: bool) -> bool:
    """Check if client matches all filters."""
    if not _client_matches_mode(client, client_mode):
        return False
    if only_unifi and not client_is_unifi(client):
        return False
    return True


def _client_attachment(client: object, device_index: dict[str, str]) -> tuple[str, str] | None:
    cid = client_node_id(client)
    if not cid:
        return None
    uplink_mac = client_uplink_mac(client)
    if not uplink_mac:
        return None
    device_id = normalize_mac(uplink_mac)
    if device_id not in device_index:
        return None
    return device_id, cid


def _client_edge_label(device_display: str, client_display: str, client: object) -> str | None:
    uplink_port = client_uplink_port(client)
    if uplink_port is None:
        return None
    return f"{device_display}: Port {uplink_port} <-> {client_display}"


def _client_vlans(client: object) -> tuple[int, ...]:
    client_vlan = _client_vlan(client)
    if client_vlan is None:
        return ()
    return (client_vlan,)


def _client_edge(
    device_id: str,
    client_id: str,
    client: object,
    *,
    include_ports: bool,
    node_names: dict[str, str] | None = None,
) -> Edge:
    names = node_names or {}
    device_display = names.get(device_id, device_id)
    client_display = names.get(client_id, client_id)
    is_wireless = not _client_is_wired(client)
    vlans = _client_vlans(client)
    return Edge(
        left=device_id,
        right=client_id,
        label=_client_edge_label(device_display, client_display, client) if include_ports else None,
        wireless=is_wireless,
        channel=_client_channel(client) if is_wireless else None,
        vlans=vlans,
        active_vlans=vlans,
        is_trunk=False,
        connection=_extract_connection_info(client),
    )


def _add_attachment_key(seen: set[tuple[str, str]], attachment: tuple[str, str]) -> bool:
    if attachment in seen:
        return False
    seen.add(attachment)
    return True


def build_client_edges(
    clients: Iterable[object],
    device_index: dict[str, str],
    *,
    include_ports: bool = False,
    client_mode: str = "wired",
    only_unifi: bool = False,
    node_names: dict[str, str] | None = None,
) -> list[Edge]:
    """Build edges from devices to their connected clients."""
    edges: list[Edge] = []
    seen: set[tuple[str, str]] = set()
    for client in clients:
        if not client_matches_filters(client, client_mode=client_mode, only_unifi=only_unifi):
            continue
        attachment = _client_attachment(client, device_index)
        if attachment is None:
            continue
        if not _add_attachment_key(seen, attachment):
            continue
        device_id, client_id = attachment
        edges.append(
            _client_edge(
                device_id,
                client_id,
                client,
                include_ports=include_ports,
                node_names=node_names,
            )
        )
    return edges


def _device_node_types(devices: Iterable[Device]) -> dict[str, str]:
    return {normalize_mac(device.mac): classify_device_type(device) for device in devices}


def _client_node_types(
    clients: Iterable[object],
    *,
    client_mode: str,
    only_unifi: bool,
) -> dict[str, str]:
    node_types: dict[str, str] = {}
    for client in clients:
        if not client_matches_filters(client, client_mode=client_mode, only_unifi=only_unifi):
            continue
        cid = client_node_id(client)
        if cid:
            node_types[cid] = classify_client_type(client)
    return node_types


def build_node_type_map(
    devices: Iterable[Device],
    clients: Iterable[object] | None = None,
    *,
    client_mode: str = "wired",
    only_unifi: bool = False,
) -> dict[str, str]:
    """Build a map of node names to their types."""
    node_types = _device_node_types(devices)
    if clients:
        node_types.update(
            _client_node_types(
                clients,
                client_mode=client_mode,
                only_unifi=only_unifi,
            )
        )
    return node_types


def build_client_port_map(
    devices: Iterable[Device],
    clients: Iterable[object],
    *,
    client_mode: str,
    only_unifi: bool = False,
) -> ClientPortMap:
    """Build a map of device IDs (MACs) to their connected client ports."""
    from .topology import build_device_index

    device_index = build_device_index(devices)
    port_map: ClientPortMap = {}
    for client in clients:
        if not client_matches_filters(client, client_mode=client_mode, only_unifi=only_unifi):
            continue
        attachment = _client_attachment(client, device_index)
        uplink_port = client_uplink_port(client)
        if attachment is None or uplink_port is None:
            continue
        device_id, client_id = attachment
        port_map.setdefault(device_id, []).append((uplink_port, client_id))
    return port_map


def _partition_client_edges(
    edges: list[Edge],
    node_types: dict[str, str],
) -> tuple[list[Edge], dict[str, int], set[str]]:
    client_counts: dict[str, int] = {}
    non_client_edges: list[Edge] = []
    collapsed_clients: set[str] = set()
    for edge in edges:
        if node_types.get(edge.right) == "client":
            client_counts[edge.left] = client_counts.get(edge.left, 0) + 1
            collapsed_clients.add(edge.right)
        else:
            non_client_edges.append(edge)
    return non_client_edges, client_counts, collapsed_clients


class CollapsedClientEdges(NamedTuple):
    edges: list[Edge]
    client_counts: dict[str, int]
    node_types: dict[str, str]
    node_names: dict[str, str]


def collapse_client_edges(
    edges: list[Edge],
    node_types: dict[str, str],
    node_names: dict[str, str] | None = None,
) -> CollapsedClientEdges:
    """Collapse individual client edges into cluster nodes.

    Pure: the input maps are not mutated. Returns the collapsed edges, per-device
    client counts, and fresh node_types/node_names maps with client nodes removed
    and cluster nodes added.
    """
    types = dict(node_types)
    names = dict(node_names or {})
    collapsed_edges, client_counts, collapsed_clients = _partition_client_edges(edges, types)

    for client_id in collapsed_clients:
        types.pop(client_id, None)

    for device_id, count in sorted(client_counts.items()):
        cluster_id = f"{device_id}__cluster"
        device_display = names.get(device_id, device_id)
        collapsed_edges.append(Edge(left=device_id, right=cluster_id))
        types[cluster_id] = "client_cluster"
        names[cluster_id] = f"{device_display} ({count} clients)"

    return CollapsedClientEdges(collapsed_edges, client_counts, types, names)
