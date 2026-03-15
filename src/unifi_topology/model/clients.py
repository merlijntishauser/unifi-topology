"""Client handling and edge building."""

from __future__ import annotations

from collections.abc import Iterable

from . import _client_access
from .classify import (
    classify_client_type,
    classify_device_type,
    client_display_name,
    client_is_unifi,
)
from .helpers import normalize_mac
from .topology import ClientPortMap, Device, Edge

_client_channel = _client_access._client_channel
_client_is_wired = _client_access._client_is_wired
_client_vlan = _client_access._client_vlan
_extract_connection_info = _client_access._extract_connection_info
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
    name = client_display_name(client)
    uplink_mac = client_uplink_mac(client)
    if not name or not uplink_mac:
        return None
    device_name = device_index.get(normalize_mac(uplink_mac))
    if not device_name:
        return None
    return device_name, name


def _client_edge_label(device_name: str, client_name: str, client: object) -> str | None:
    uplink_port = client_uplink_port(client)
    if uplink_port is None:
        return None
    return f"{device_name}: Port {uplink_port} <-> {client_name}"


def _client_vlans(client: object) -> tuple[int, ...]:
    client_vlan = _client_vlan(client)
    if client_vlan is None:
        return ()
    return (client_vlan,)


def _client_edge(
    device_name: str,
    name: str,
    client: object,
    *,
    include_ports: bool,
) -> Edge:
    is_wireless = not _client_is_wired(client)
    vlans = _client_vlans(client)
    return Edge(
        left=device_name,
        right=name,
        label=_client_edge_label(device_name, name, client) if include_ports else None,
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
        device_name, name = attachment
        edges.append(_client_edge(device_name, name, client, include_ports=include_ports))
    return edges


def _device_node_types(devices: Iterable[Device]) -> dict[str, str]:
    return {device.name: classify_device_type(device) for device in devices}


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
        name = client_display_name(client)
        if name:
            node_types[name] = classify_client_type(client)
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
    """Build a map of device names to their connected client ports."""
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
        device_name, name = attachment
        port_map.setdefault(device_name, []).append((uplink_port, name))
    return port_map


def collapse_client_edges(
    edges: list[Edge],
    node_types: dict[str, str],
) -> tuple[list[Edge], dict[str, int]]:
    """Collapse individual client edges into cluster nodes."""
    client_counts: dict[str, int] = {}
    collapsed_edges: list[Edge] = []
    collapsed_clients: set[str] = set()

    for edge in edges:
        if node_types.get(edge.right) == "client":
            client_counts[edge.left] = client_counts.get(edge.left, 0) + 1
            collapsed_clients.add(edge.right)
        else:
            collapsed_edges.append(edge)

    for client_name in collapsed_clients:
        node_types.pop(client_name, None)

    for device_name, count in sorted(client_counts.items()):
        cluster_name = f"{device_name} ({count} clients)"
        collapsed_edges.append(
            Edge(
                left=device_name,
                right=cluster_name,
                label=None,
                poe=False,
                wireless=False,
            )
        )
        node_types[cluster_name] = "client_cluster"

    return collapsed_edges, client_counts
