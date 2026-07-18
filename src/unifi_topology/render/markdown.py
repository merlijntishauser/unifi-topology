"""Render per-device port overview tables."""

from __future__ import annotations

from ..model.classify import classify_device_type
from ..model.topology import ClientPortMap, Device, PortInfo, PortMap
from ._device_ports_aggregate import (
    aggregate_ports,
    aggregate_sort_key,
    format_aggregate_label,
    port_index,
)
from ._device_summary import poe_summary, port_summary, uplink_summary
from ._markdown_connections import (
    device_client_connections,
    device_port_connections,
    format_aggregate_connections,
    format_connections,
)
from ._markdown_port_format import (
    format_aggregate_poe_state,
    format_aggregate_power,
    format_aggregate_speed,
    format_poe_power,
    format_poe_state,
    format_port_label,
    format_speed,
    port_sort_key,
)
from ._markdown_tables import escape_markdown, markdown_table_lines
from ._templating import render_template


def render_device_port_overview(
    devices: list[Device],
    port_map: PortMap,
    *,
    client_ports: ClientPortMap | None = None,
) -> str:
    gateways = _collect_devices_by_type(devices, "gateway")
    switches = _collect_devices_by_type(devices, "switch")
    sections: list[str] = []
    _append_device_section(sections, "Gateways", gateways, port_map, client_ports)
    _append_device_section(sections, "Switches", switches, port_map, client_ports)
    return "\n\n".join(section for section in sections if section).rstrip() + "\n"


def _append_device_section(
    sections: list[str],
    title: str,
    devices: list[Device],
    port_map: PortMap,
    client_ports: ClientPortMap | None,
) -> None:
    if not devices:
        return
    sections.append(
        render_template(
            "markdown_section.md.j2",
            title=title,
            body=_render_device_group(devices, port_map, client_ports),
        ).rstrip()
    )


def _collect_devices_by_type(devices: list[Device], desired_type: str) -> list[Device]:
    return sorted(
        [device for device in devices if classify_device_type(device) == desired_type],
        key=lambda item: item.name.lower(),
    )


def _render_device_group(
    devices: list[Device],
    port_map: PortMap,
    client_ports: ClientPortMap | None,
) -> str:
    blocks: list[str] = []
    for device in devices:
        blocks.append(
            render_template(
                "device_port_block.md.j2",
                device_name=device.name,
                details="\n".join(_render_device_details(device)).rstrip(),
                ports="\n".join(_render_device_ports(device, port_map, client_ports)).rstrip(),
            ).rstrip()
        )
    return "\n\n".join(block for block in blocks if block)


def render_device_port_details(
    device: Device,
    port_map: PortMap,
    *,
    client_ports: ClientPortMap | None = None,
) -> str:
    lines = _render_device_details(device)
    lines.extend(_render_device_ports(device, port_map, client_ports))
    return "\n".join(lines).rstrip() + "\n"


def render_device_port_table(
    device: Device,
    port_map: PortMap,
    *,
    client_ports: ClientPortMap | None = None,
) -> str:
    """Render only the per-port table for a device, without the details table."""
    lines = _render_device_ports(device, port_map, client_ports)
    return "\n".join(lines).rstrip() + "\n"


def _render_device_ports(
    device: Device,
    port_map: PortMap,
    client_ports: ClientPortMap | None,
) -> list[str]:
    rows = _build_port_rows(device, port_map, client_ports)
    table_rows = [
        [
            escape_markdown(port_label),
            connected or "-",
            escape_markdown(speed),
            escape_markdown(poe_state),
            escape_markdown(power),
        ]
        for port_label, connected, speed, poe_state, power in rows
    ]
    lines = ["#### Ports", ""]
    lines.extend(
        markdown_table_lines(
            ["Port", "Connected", "Speed", "PoE", "Power"],
            table_rows,
        )
    )
    return lines


_SortedRow = tuple[tuple[int, int], tuple[str, str, str, str, str]]


def _build_individual_port_rows(
    device: Device,
    aggregated_indices: set[int],
    connections: dict[int, list[str]],
    client_connections: dict[int, list[str]],
    port_map: PortMap,
) -> tuple[list[_SortedRow], set[int]]:
    rows: list[_SortedRow] = []
    seen_ports: set[int] = set()
    for port in sorted(device.port_table, key=port_sort_key):
        row_result = _process_individual_port(
            port,
            device.name,
            aggregated_indices,
            connections,
            client_connections,
            port_map,
        )
        if row_result is None:
            continue
        idx, row = row_result
        if idx is not None:
            seen_ports.add(idx)
        rows.append(row)
    return rows, seen_ports


def _process_individual_port(
    port: PortInfo,
    device_name: str,
    aggregated_indices: set[int],
    connections: dict[int, list[str]],
    client_connections: dict[int, list[str]],
    port_map: PortMap,
) -> tuple[int | None, _SortedRow] | None:
    idx = port_index(port.port_idx, port.name)
    if port.port_idx in aggregated_indices:
        return None
    port_label = format_port_label(idx, port.name)
    connected = format_connections(device_name, idx, connections, client_connections, port_map)
    row: _SortedRow = (
        (0, idx or 10_000),
        (
            port_label,
            connected,
            format_speed(port.speed),
            format_poe_state(port),
            format_poe_power(port.poe_power),
        ),
    )
    return idx, row


def _build_aggregate_rows(
    device_name: str,
    aggregated: dict[str, list[PortInfo]],
    connections: dict[int, list[str]],
    client_connections: dict[int, list[str]],
    port_map: PortMap,
) -> list[_SortedRow]:
    rows: list[_SortedRow] = []
    for _group_id, group_ports in aggregated.items():
        group_connections = format_aggregate_connections(
            device_name,
            group_ports,
            connections,
            client_connections,
            port_map,
        )
        rows.append(
            (
                (0, aggregate_sort_key(group_ports)),
                (
                    format_aggregate_label(group_ports),
                    group_connections,
                    format_aggregate_speed(group_ports),
                    format_aggregate_poe_state(group_ports),
                    format_aggregate_power(group_ports),
                ),
            )
        )
    return rows


def _build_orphan_connection_rows(
    device_name: str,
    connections: dict[int, list[str]],
    client_connections: dict[int, list[str]],
    seen_ports: set[int],
    port_map: PortMap,
) -> list[_SortedRow]:
    rows: list[_SortedRow] = []
    for pidx in sorted(connections):
        if pidx in seen_ports:
            continue
        port_label = format_port_label(pidx, None)
        connected = format_connections(
            device_name,
            pidx,
            connections,
            client_connections,
            port_map,
        )
        rows.append(((2, pidx), (port_label, connected, "-", "-", "-")))
    return rows


def _build_port_rows(
    device: Device,
    port_map: PortMap,
    client_ports: ClientPortMap | None,
) -> list[tuple[str, str, str, str, str]]:
    connections = device_port_connections(device.name, port_map)
    client_connections = device_client_connections(device.name, client_ports)
    aggregated = aggregate_ports(device.port_table)
    aggregated_indices = _collect_aggregated_indices(aggregated)
    rows: list[_SortedRow] = []
    individual, seen_ports = _build_individual_port_rows(
        device,
        aggregated_indices,
        connections,
        client_connections,
        port_map,
    )
    rows.extend(individual)
    rows.extend(
        _build_aggregate_rows(device.name, aggregated, connections, client_connections, port_map)
    )
    rows.extend(
        _build_orphan_connection_rows(
            device.name,
            connections,
            client_connections,
            seen_ports,
            port_map,
        )
    )
    return [row for _key, row in sorted(rows, key=lambda item: item[0])]


def _collect_aggregated_indices(aggregated: dict[str, list[PortInfo]]) -> set[int]:
    return {
        port.port_idx
        for ports in aggregated.values()
        for port in ports
        if port.port_idx is not None
    }


def _render_device_details(device: Device) -> list[str]:
    return [
        "#### Details",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Model | {escape_markdown(_device_model_label(device))} |",
        f"| Type | {escape_markdown(device.type or '-')} |",
        f"| IP | {escape_markdown(device.ip or '-')} |",
        f"| MAC | {escape_markdown(device.mac or '-')} |",
        f"| Firmware | {escape_markdown(device.version or '-')} |",
        f"| Uplink | {escape_markdown(uplink_summary(device))} |",
        f"| Ports | {escape_markdown(port_summary(device))} |",
        f"| PoE | {escape_markdown(poe_summary(device))} |",
        "",
    ]


def _device_model_label(device: Device) -> str:
    if device.model_name:
        return device.model_name
    if device.model:
        return device.model
    return device.type or "-"
