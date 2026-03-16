"""Shared device summary helpers for markdown renderers."""

from __future__ import annotations

from ..model.classify import classify_device_type
from ..model.topology import Device, PortInfo


def _indexed_ports(device: Device) -> list[PortInfo]:
    return [port for port in device.port_table if port.port_idx is not None]


def port_summary(device: Device) -> str:
    """Summarize port count and activity for a device."""
    ports = _indexed_ports(device)
    if not ports:
        return "-"
    total_ports = len(ports)
    active_ports = sum(1 for port in ports if (port.speed or 0) > 0)
    return f"{total_ports} total, {active_ports} active"


def _poe_capable_count(ports: list[PortInfo]) -> int:
    return sum(1 for port in ports if port.port_poe or port.poe_enable)


def _poe_active_count(ports: list[PortInfo]) -> int:
    return sum(1 for port in ports if _is_poe_active(port))


def _poe_total_power(ports: list[PortInfo]) -> float:
    return sum(port.poe_power or 0.0 for port in ports)


def poe_summary(device: Device) -> str:
    """Summarize PoE capability, activity, and power draw."""
    ports = _indexed_ports(device)
    if not ports:
        return "-"
    summary = f"{_poe_capable_count(ports)} capable, {_poe_active_count(ports)} active"
    total_power = _poe_total_power(ports)
    if total_power > 0:
        summary = f"{summary}, {total_power:.2f}W"
    return summary


def _format_uplink_label(name: str, port: int | None) -> str:
    if port is not None:
        return f"{name} (Port {port})"
    return name


def uplink_summary(device: Device) -> str:
    """Describe the device's uplink connection."""
    uplink = device.uplink or device.last_uplink
    if not uplink:
        return _uplink_fallback(device)
    name = _resolve_uplink_name(device, uplink.name or uplink.mac or "Unknown")
    return _format_uplink_label(name, uplink.port)


def _uplink_fallback(device: Device) -> str:
    if classify_device_type(device) == "gateway":
        return "Internet"
    return "-"


def _resolve_uplink_name(device: Device, raw_name: str) -> str:
    if classify_device_type(device) != "gateway":
        return raw_name
    return _normalize_gateway_uplink(raw_name)


def _normalize_gateway_uplink(raw_name: str) -> str:
    lowered = raw_name.lower()
    if lowered in {"unknown", "wan", "internet"}:
        return "Internet"
    if lowered.startswith(("eth", "wan")):
        return "Internet"
    return raw_name


def _is_poe_active(port: PortInfo) -> bool:
    return (port.poe_power or 0.0) > 0 or port.poe_good
