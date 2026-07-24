"""Connection formatting helpers for Markdown device tables."""

from __future__ import annotations

from collections import defaultdict

from ..model.ports import extract_port_number
from ..model.topology import ClientPortMap, PortInfo, PortMap
from ._device_ports_aggregate import port_index
from ._markdown_tables import escape_markdown


def port_map_by_name(port_map: PortMap, name_of: dict[str, str]) -> PortMap:
    """Rewrite a MAC-keyed device port map to use display names.

    ``name_of`` maps a node id (MAC) to its display name; unknown ids are left
    as-is. The connection helpers key on display name, so a MAC-keyed map (as
    ``build_port_map`` produces) must be translated before rendering.
    """
    return {
        (name_of.get(src, src), name_of.get(dst, dst)): label
        for (src, dst), label in port_map.items()
    }


def client_port_map_by_name(
    client_map: ClientPortMap,
    name_of: dict[str, str],
    client_names: dict[str, str],
) -> ClientPortMap:
    """Rewrite a MAC-keyed client port map to device/client display names."""
    result: ClientPortMap = {}
    for device_id, rows in client_map.items():
        device_name = name_of.get(device_id, device_id)
        result[device_name] = [
            (port, client_names.get(client_id, client_id)) for port, client_id in rows
        ]
    return result


def device_port_connections(device_name: str, port_map: PortMap) -> dict[int, list[str]]:
    connections: dict[int, list[str]] = defaultdict(list)
    for (src, dst), label in port_map.items():
        if src != device_name:
            continue
        port_idx = extract_port_number(label or "")
        if port_idx is not None:
            connections[port_idx].append(dst)
    return connections


def device_client_connections(
    device_name: str, client_ports: ClientPortMap | None
) -> dict[int, list[str]]:
    if not client_ports:
        return {}
    rows = client_ports.get(device_name, [])
    connections: dict[int, list[str]] = defaultdict(list)
    for port_idx, name in rows:
        connections[port_idx].append(name)
    return connections


def format_connections(
    device_name: str,
    port_idx: int | None,
    connections: dict[int, list[str]],
    client_connections: dict[int, list[str]],
    port_map: PortMap,
) -> str:
    if port_idx is None:
        return ""
    peers = connections.get(port_idx, [])
    clients = client_connections.get(port_idx, [])
    if not peers and not clients:
        return ""
    peer_text = _format_peer_entries(peers, device_name, port_map)
    client_text = _format_client_connections(clients)
    return _combine_connection_texts(peer_text, client_text)


def _format_peer_entries(
    peers: list[str],
    device_name: str,
    port_map: PortMap,
) -> str:
    entries: list[str] = []
    for peer in sorted(peers, key=str.lower):
        peer_label = port_map.get((peer, device_name))
        if peer_label:
            entries.append(f"{escape_markdown(peer)} ({escape_markdown(peer_label)})")
        else:
            entries.append(escape_markdown(peer))
    return ", ".join(entries)


def _combine_connection_texts(peer_text: str, client_text: str) -> str:
    if peer_text and client_text:
        return f"{peer_text}<br/>{client_text}"
    return peer_text or client_text


def _format_client_connections(clients: list[str]) -> str:
    if not clients:
        return ""
    if len(clients) == 1:
        return f"{escape_markdown(clients[0])} (client)"
    items = "".join(f"<li>{escape_markdown(name)}</li>" for name in clients)
    return f'<ul class="unifi-port-clients">{items}</ul>'


def port_connection_text(
    port: PortInfo,
    device_name: str,
    connections: dict[int, list[str]],
    client_connections: dict[int, list[str]],
    port_map: PortMap,
) -> str | None:
    idx = port_index(port.port_idx, port.name)
    if idx is None:
        return None
    text = format_connections(device_name, idx, connections, client_connections, port_map)
    return text or None


def format_aggregate_connections(
    device_name: str,
    group_ports: list[PortInfo],
    connections: dict[int, list[str]],
    client_connections: dict[int, list[str]],
    port_map: PortMap,
) -> str:
    rendered = [
        text
        for port in group_ports
        if (
            text := port_connection_text(
                port, device_name, connections, client_connections, port_map
            )
        )
    ]
    return ", ".join(rendered)
