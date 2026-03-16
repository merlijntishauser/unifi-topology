"""Port aggregation (LAG) detection and formatting."""

from __future__ import annotations

from collections import defaultdict

from ..model.ports import extract_port_number
from ..model.topology import PortInfo


def looks_like_lag(port: PortInfo) -> bool:
    name = (port.name or "").lower()
    ifname = (port.ifname or "").lower()
    return "lag" in name or "lag" in ifname or "aggregate" in name


def aggregate_base_groups(port_table: list[PortInfo]) -> dict[str, list[PortInfo]]:
    groups: dict[str, list[PortInfo]] = defaultdict(list)
    for port in port_table:
        _classify_port_into_group(port, groups)
    return groups


def _classify_port_into_group(port: PortInfo, groups: dict[str, list[PortInfo]]) -> None:
    if port.aggregation_group:
        groups[str(port.aggregation_group)].append(port)
    elif looks_like_lag(port) and port.port_idx is not None:
        groups[f"lag-{port.port_idx}"].append(port)


def _is_valid_lag_neighbor(port: PortInfo | None, speed: int | None) -> bool:
    if port is None:
        return False
    return not port.aggregation_group and port.speed == speed


def _find_lag_neighbors(
    lone_port: PortInfo,
    port_by_idx: dict[int, PortInfo],
) -> list[PortInfo]:
    port_idx = lone_port.port_idx
    if port_idx is None:
        return []
    return [
        port_by_idx[idx]
        for idx in (port_idx - 1, port_idx + 1)
        if _is_valid_lag_neighbor(port_by_idx.get(idx), lone_port.speed)
    ]


def _build_port_index(port_table: list[PortInfo]) -> dict[int, PortInfo]:
    return {port.port_idx: port for port in port_table if port.port_idx is not None}


def extend_singleton_groups(
    groups: dict[str, list[PortInfo]],
    port_table: list[PortInfo],
) -> None:
    if not groups:
        return
    port_by_idx = _build_port_index(port_table)
    for group_id, group_ports in list(groups.items()):
        _try_extend_singleton(group_id, group_ports, groups, port_by_idx)


def _try_extend_singleton(
    group_id: str,
    group_ports: list[PortInfo],
    groups: dict[str, list[PortInfo]],
    port_by_idx: dict[int, PortInfo],
) -> None:
    if len(group_ports) != 1 or not looks_like_lag(group_ports[0]):
        return
    candidates = _find_lag_neighbors(group_ports[0], port_by_idx)
    if candidates:
        groups[group_id].extend(candidates)


def aggregate_ports(port_table: list[PortInfo]) -> dict[str, list[PortInfo]]:
    """Group ports by aggregation/LAG membership."""
    groups = aggregate_base_groups(port_table)
    extend_singleton_groups(groups, port_table)
    return groups


def aggregate_sort_key(group_ports: list[PortInfo]) -> int:
    ports = sorted([int(p.port_idx) for p in group_ports if p.port_idx is not None])
    return ports[0] if ports else 10_000


def _sorted_port_indices(group_ports: list[PortInfo]) -> list[int]:
    return sorted([int(p.port_idx) for p in group_ports if p.port_idx is not None])


def _format_port_range(ports: list[int]) -> str:
    if ports == list(range(ports[0], ports[-1] + 1)):
        return f"Port {ports[0]}-{ports[-1]} (LAG)"
    return "Ports " + "+".join(str(port) for port in ports) + " (LAG)"


def format_aggregate_label(group_ports: list[PortInfo]) -> str:
    ports = _sorted_port_indices(group_ports)
    if not ports:
        return "Aggregated ports"
    if len(ports) == 1:
        return f"Port {ports[0]} (LAG)"
    return _format_port_range(ports)


def port_index(port_idx: int | None, name: str | None) -> int | None:
    if port_idx is not None:
        return port_idx
    if name:
        return extract_port_number(name)
    return None
