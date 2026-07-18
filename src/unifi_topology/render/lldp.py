"""Render LLDP data as Markdown tables."""

from __future__ import annotations

from collections.abc import Iterable

from ..model._client_access import client_node_id
from ..model.classify import client_display_name
from ..model.clients import (
    build_client_port_map,
    client_matches_filters,
    client_uplink_mac,
    client_uplink_port,
)
from ..model.edges import build_device_index, build_port_map
from ..model.helpers import normalize_mac
from ..model.lldp import LLDPEntry, local_port_label
from ..model.topology import Device
from ._device_summary import poe_summary, port_summary, uplink_summary
from ._markdown_tables import escape_markdown, markdown_table_lines
from ._templating import render_template
from .markdown import render_device_port_details


def _lldp_sort_key(entry: LLDPEntry) -> tuple[int, str, str]:
    port_label = local_port_label(entry) or ""
    port_number = "".join(ch for ch in port_label if ch.isdigit())
    return (int(port_number or 0), port_label, entry.port_id)


def _client_summary(
    device: Device, client_rows: dict[str, list[tuple[str, str | None]]]
) -> tuple[str, str]:
    rows = client_rows.get(device.name)
    if rows is None:
        return "-", "-"
    count = len(rows)
    names = [name for name, _port in rows]
    sample = ", ".join(names[:3])
    if len(names) > 3:
        sample = f"{sample}, ..."
    return str(count), sample or "-"


def _esc(value: str | None) -> str:
    return escape_markdown(value or "-")


def _device_identity_rows(device: Device) -> list[list[str]]:
    return [
        ["Model", _esc(device.model_name or device.type)],
        ["Type", _esc(device.type)],
        ["IP", _esc(device.ip)],
        ["MAC", _esc(device.mac)],
        ["Firmware", _esc(device.version)],
    ]


def _device_detail_rows(device: Device) -> list[list[str]]:
    rows = _device_identity_rows(device)
    rows.append(["Uplink", escape_markdown(uplink_summary(device))])
    rows.append(["Ports", escape_markdown(port_summary(device))])
    rows.append(["PoE", escape_markdown(poe_summary(device))])
    return rows


def _details_table_lines(
    device: Device,
    client_rows: dict[str, list[tuple[str, str | None]]],
    client_mode: str,
) -> list[str]:
    wired_count, client_sample = _client_summary(device, client_rows)
    rows = _device_detail_rows(device)
    rows.append([f"Clients ({client_mode})", escape_markdown(wired_count)])
    rows.append(["Client examples", escape_markdown(client_sample)])
    lines = ["### Details", ""]
    lines.extend(markdown_table_lines(["Field", "Value"], rows))
    return lines


def _lldp_entry_row(entry: LLDPEntry, device_index: dict[str, str]) -> list[str]:
    local_label = local_port_label(entry) or "?"
    peer_name = device_index.get(normalize_mac(entry.chassis_id), "")
    return [
        local_label,
        peer_name or "-",
        entry.port_id or "?",
        entry.chassis_id,
        entry.port_desc or "-",
    ]


def _lldp_rows(
    entries: Iterable[LLDPEntry],
    device_index: dict[str, str],
) -> list[list[str]]:
    return [_lldp_entry_row(entry, device_index) for entry in sorted(entries, key=_lldp_sort_key)]


def _collect_client_row(
    client: object,
    device_index: dict[str, str],
    *,
    include_ports: bool,
) -> tuple[str, str | None, str] | None:
    name = client_display_name(client)
    uplink_mac = client_uplink_mac(client)
    if not name or not uplink_mac:
        return None
    device_name = device_index.get(normalize_mac(uplink_mac))
    if not device_name:
        return None
    port_label = _resolve_port_label(client, include_ports)
    return name, port_label, device_name


def _resolve_port_label(client: object, include_ports: bool) -> str | None:
    if not include_ports:
        return None
    port = client_uplink_port(client)
    if port is not None:
        return f"Port {port}"
    return None


def _client_rows(
    clients: Iterable[object],
    device_index: dict[str, str],
    *,
    include_ports: bool,
    client_mode: str,
    only_unifi: bool,
) -> dict[str, list[tuple[str, str | None]]]:
    rows_by_device: dict[str, list[tuple[str, str | None]]] = {}
    for client in clients:
        if not client_matches_filters(client, client_mode=client_mode, only_unifi=only_unifi):
            continue
        result = _collect_client_row(client, device_index, include_ports=include_ports)
        if result is None:
            continue
        name, port_label, device_name = result
        rows_by_device.setdefault(device_name, []).append((name, port_label))
    return rows_by_device


def _prepare_lldp_maps(
    devices: list[Device],
    *,
    clients: Iterable[object] | None,
    include_ports: bool,
    show_clients: bool,
    client_mode: str,
    only_unifi: bool,
) -> tuple[
    dict[tuple[str, str], str],
    dict[str, list[tuple[int, str]]] | None,
    dict[str, list[tuple[str, str | None]]],
]:
    device_index = build_device_index(devices)
    client_rows = _build_client_rows(
        clients,
        device_index,
        include_ports=include_ports,
        client_mode=client_mode,
        only_unifi=only_unifi,
    )
    port_map, client_port_map = _build_port_maps(
        devices,
        clients,
        include_ports=include_ports,
        show_clients=show_clients,
        client_mode=client_mode,
        only_unifi=only_unifi,
    )
    return port_map, client_port_map, client_rows


def _build_client_rows(
    clients: Iterable[object] | None,
    device_index: dict[str, str],
    *,
    include_ports: bool,
    client_mode: str,
    only_unifi: bool,
) -> dict[str, list[tuple[str, str | None]]]:
    if not clients:
        return {}
    return _client_rows(
        clients,
        device_index,
        include_ports=include_ports,
        client_mode=client_mode,
        only_unifi=only_unifi,
    )


def _build_port_maps(
    devices: list[Device],
    clients: Iterable[object] | None,
    *,
    include_ports: bool,
    show_clients: bool,
    client_mode: str,
    only_unifi: bool,
) -> tuple[dict[tuple[str, str], str], dict[str, list[tuple[int, str]]] | None]:
    if not include_ports:
        return {}, None
    name_of = build_device_index(devices)
    port_map = _port_map_by_name(build_port_map(devices, only_unifi=False), name_of)
    client_port_map = None
    if clients and show_clients:
        raw_client_map = build_client_port_map(
            devices,
            clients,
            client_mode=client_mode,
            only_unifi=only_unifi,
        )
        client_port_map = _client_port_map_by_name(
            raw_client_map, name_of, _client_name_index(clients)
        )
    return port_map, client_port_map


def _client_name_index(clients: Iterable[object]) -> dict[str, str]:
    """Map each client's node id (MAC) to its display name."""
    index: dict[str, str] = {}
    for client in clients:
        node_id = client_node_id(client)
        if node_id:
            index[node_id] = client_display_name(client) or node_id
    return index


def _port_map_by_name(
    port_map: dict[tuple[str, str], str],
    name_of: dict[str, str],
) -> dict[tuple[str, str], str]:
    """Rewrite a MAC-keyed device port map to use display names."""
    return {
        (name_of.get(src, src), name_of.get(dst, dst)): label
        for (src, dst), label in port_map.items()
    }


def _client_port_map_by_name(
    client_map: dict[str, list[tuple[int, str]]],
    name_of: dict[str, str],
    client_names: dict[str, str],
) -> dict[str, list[tuple[int, str]]]:
    """Rewrite a MAC-keyed client port map to device/client display names."""
    result: dict[str, list[tuple[int, str]]] = {}
    for device_id, rows in client_map.items():
        device_name = name_of.get(device_id, device_id)
        result[device_name] = [
            (port, client_names.get(client_id, client_id)) for port, client_id in rows
        ]
    return result


def _render_lldp_table(
    device: Device,
    device_index: dict[str, str],
) -> str:
    if device.lldp_info:
        return "\n".join(
            markdown_table_lines(
                ["Local Port", "Neighbor", "Neighbor Port", "Chassis ID", "Port Description"],
                _lldp_rows(device.lldp_info, device_index),
                escape=escape_markdown,
            )
        ).rstrip()
    return "_No LLDP neighbors._"


def _render_clients_section(
    device: Device,
    client_rows: dict[str, list[tuple[str, str | None]]],
    *,
    include_ports: bool,
    show_clients: bool,
) -> str:
    rows = client_rows.get(device.name)
    if not rows or not show_clients:
        return ""
    if include_ports:
        return _render_client_table(rows)
    return _render_client_list(rows)


def _render_client_table(rows: list[tuple[str, str | None]]) -> str:
    return "\n".join(
        [
            "### Clients",
            "",
            "\n".join(
                markdown_table_lines(
                    ["Client", "Port"],
                    [
                        [escape_markdown(client_name), escape_markdown(port_label or "-")]
                        for client_name, port_label in rows
                    ],
                )
            ),
        ]
    ).rstrip()


def _render_client_list(rows: list[tuple[str, str | None]]) -> str:
    return "\n".join(["### Clients", *[f"- {escape_markdown(name)}" for name, _ in rows]]).rstrip()


def _render_ports_section(
    device: Device,
    port_map: dict[tuple[str, str], str],
    client_port_map: dict[str, list[tuple[int, str]]] | None,
    *,
    include_ports: bool,
) -> str:
    if not include_ports:
        return ""
    return "\n".join(
        [
            "### Ports",
            "",
            render_device_port_details(device, port_map, client_ports=client_port_map).strip(),
        ]
    ).rstrip()


def _render_device_lldp_section(
    device: Device,
    *,
    device_index: dict[str, str],
    port_map: dict[tuple[str, str], str],
    client_port_map: dict[str, list[tuple[int, str]]] | None,
    client_rows: dict[str, list[tuple[str, str | None]]],
    include_ports: bool,
    show_clients: bool,
    client_mode: str,
) -> str:
    details = "\n".join(_details_table_lines(device, client_rows, client_mode)).rstrip()
    ports_section = _render_ports_section(
        device,
        port_map,
        client_port_map,
        include_ports=include_ports,
    )
    lldp_section = _render_lldp_table(device, device_index)
    clients_section = _render_clients_section(
        device,
        client_rows,
        include_ports=include_ports,
        show_clients=show_clients,
    )
    return render_template(
        "lldp_device_section.md.j2",
        device_name=device.name,
        details=details,
        ports_section=ports_section,
        lldp_section=lldp_section,
        clients_section=clients_section,
    ).rstrip()


def render_lldp_md(
    devices: list[Device],
    *,
    clients: Iterable[object] | None = None,
    include_ports: bool = False,
    show_clients: bool = False,
    client_mode: str = "wired",
    only_unifi: bool = False,
) -> str:
    device_index = build_device_index(devices)
    port_map, client_port_map, client_rows = _prepare_lldp_maps(
        devices,
        clients=clients,
        include_ports=include_ports,
        show_clients=show_clients,
        client_mode=client_mode,
        only_unifi=only_unifi,
    )
    sections: list[str] = []
    for device in sorted(devices, key=lambda item: item.name.lower()):
        sections.append(
            _render_device_lldp_section(
                device,
                device_index=device_index,
                port_map=port_map,
                client_port_map=client_port_map,
                client_rows=client_rows,
                include_ports=include_ports,
                show_clients=show_clients,
                client_mode=client_mode,
            )
        )
    body = "\n\n".join(section for section in sections if section).rstrip()
    return (
        render_template(
            "markdown_section.md.j2",
            title="LLDP Neighbors",
            body=body,
        ).rstrip()
        + "\n"
    )
