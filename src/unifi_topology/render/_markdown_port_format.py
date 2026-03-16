"""Port formatting helpers for Markdown device tables."""

from __future__ import annotations

from ..model.topology import PortInfo
from ._device_ports_aggregate import port_index


def format_port_label(port_idx: int | None, name: str | None) -> str:
    if name and name.strip():
        return _format_named_port(port_idx, name.strip())
    if port_idx is None:
        return "Port ?"
    return f"Port {port_idx}"


def _format_named_port(port_idx: int | None, normalized: str) -> str:
    if port_idx is None:
        return normalized
    if normalized.lower() != f"port {port_idx}".lower():
        return normalized
    return f"Port {port_idx}"


def format_speed(speed: int | None) -> str:
    if speed is None or speed <= 0:
        return "-"
    if speed >= 1000:
        if speed % 1000 == 0:
            return f"{speed // 1000}G"
        return f"{speed / 1000:.1f}G"
    return f"{speed}M"


def is_poe_active(port: PortInfo) -> bool:
    return (port.poe_power or 0.0) > 0 or port.poe_good


def is_poe_capable(port: PortInfo) -> bool:
    return port.port_poe or port.poe_enable


def format_poe_state(port: PortInfo) -> str:
    if is_poe_active(port):
        return "active"
    if not is_poe_capable(port):
        return "-"
    return "disabled" if not port.poe_enable else "capable"


def format_poe_power(power: float | None) -> str:
    if power is None or power <= 0:
        return "-"
    return f"{power:.2f}W"


def port_sort_key(port: PortInfo) -> tuple[int, str]:
    idx = port_index(port.port_idx, port.name)
    if idx is not None:
        return (0, f"{idx:04d}")
    return (1, (port.name or "").lower())


def format_aggregate_speed(group_ports: list[PortInfo]) -> str:
    speeds = {port.speed for port in group_ports}
    speeds.discard(None)
    if not speeds:
        return "-"
    if len(speeds) == 1:
        return format_speed(next(iter(speeds)))
    return "mixed"


def format_aggregate_poe_state(group_ports: list[PortInfo]) -> str:
    states = {format_poe_state(port) for port in group_ports}
    if "active" in states:
        return "active"
    if "disabled" in states:
        return "disabled"
    if "capable" in states:
        return "capable"
    return "-"


def format_aggregate_power(group_ports: list[PortInfo]) -> str:
    total = sum(port.poe_power or 0.0 for port in group_ports)
    return format_poe_power(total)
