"""Coerce raw UniFi API responses to DeviceStats dataclasses."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .device_stats import DeviceStats, PoePortStats

_TYPE_MAP: dict[str, str] = {
    "ugw": "gateway",
    "udm": "gateway",
    "usw": "switch",
    "uap": "ap",
}


def _as_float(value: object, default: float = 0.0) -> float:
    """Coerce value to float."""
    if value is None:
        return default
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _as_int(value: object, default: int = 0) -> int:
    """Coerce value to int."""
    if value is None:
        return default
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _resolve_temperature(raw: dict[str, Any]) -> float | None:
    """Extract temperature from various UniFi API locations."""
    general = _temperature_from_general(raw)
    if general is not None:
        return general
    return _temperature_from_system_stats(raw)


def _temperature_from_general(raw: dict[str, Any]) -> float | None:
    general = raw.get("general_temperature")
    if general is None:
        return None
    try:
        return float(general)
    except (TypeError, ValueError):
        return None


def _temperature_from_system_stats(raw: dict[str, Any]) -> float | None:
    sys_stats = raw.get("system-stats", {})
    temps = sys_stats.get("temps") if isinstance(sys_stats, dict) else None
    if not isinstance(temps, dict) or not temps:
        return None
    first_value = next(iter(temps.values()))
    try:
        return float(first_value)
    except (TypeError, ValueError):
        return None


def _build_poe_ports(raw: dict[str, Any]) -> list[PoePortStats]:
    """Extract PoE port stats from port_table."""
    ports: list[PoePortStats] = []
    for port in raw.get("port_table", []):
        if not isinstance(port, dict):
            continue
        poe_mode = port.get("poe_mode")
        poe_power = port.get("poe_power")
        if poe_mode is not None and poe_power is not None:
            ports.append(
                PoePortStats(
                    port_idx=_as_int(port.get("port_idx")),
                    poe_power=_as_float(poe_power),
                    poe_mode=str(poe_mode),
                )
            )
    return ports


def _normalize_type(raw_type: str) -> str:
    """Normalize device type string."""
    return _TYPE_MAP.get(raw_type, raw_type)


def _device_system_stats(raw: dict[str, Any]) -> dict[str, Any]:
    system_stats = raw.get("system-stats", {})
    return system_stats if isinstance(system_stats, dict) else {}


def _device_byte_counters(raw: dict[str, Any]) -> tuple[object, object]:
    stat = raw.get("stat", {})
    stat_dict = stat if isinstance(stat, dict) else {}
    tx_bytes = raw.get("tx_bytes", stat_dict.get("tx_bytes", 0))
    rx_bytes = raw.get("rx_bytes", stat_dict.get("rx_bytes", 0))
    return tx_bytes, rx_bytes


def _device_poe_budget(raw: dict[str, Any]) -> float | None:
    poe_budget_raw = raw.get("total_max_power")
    if poe_budget_raw is None:
        return None
    return _as_float(poe_budget_raw)


def _build_device_stats(raw: dict[str, Any]) -> DeviceStats:
    system_stats = _device_system_stats(raw)
    tx_bytes, rx_bytes = _device_byte_counters(raw)
    return DeviceStats(
        mac=str(raw.get("mac", "")),
        name=str(raw.get("name", "")),
        model=str(raw.get("model", "")),
        type=_normalize_type(str(raw.get("type", ""))),
        uptime=_as_int(raw.get("uptime", 0)),
        cpu=_as_float(system_stats.get("cpu", 0.0)),
        mem=_as_float(system_stats.get("mem", 0.0)),
        temperature=_resolve_temperature(raw),
        tx_bytes=_as_int(tx_bytes),
        rx_bytes=_as_int(rx_bytes),
        num_sta=_as_int(raw.get("num_sta", 0)),
        version=str(raw.get("version", "")),
        poe_ports=_build_poe_ports(raw),
        poe_budget=_device_poe_budget(raw),
    )


def normalize_device_stats(raw_devices: Iterable[dict[str, Any]]) -> list[DeviceStats]:
    """Normalize raw device dicts from the UniFi API to DeviceStats dataclasses.

    Accepts the output of ``fetch_device_stats()`` and extracts CPU, memory,
    temperature, traffic counters, uptime, PoE port draw, and budget into
    typed ``DeviceStats`` objects.  Device types are normalized (ugw/udm to
    gateway, usw to switch, uap to ap).
    """
    return [_build_device_stats(raw) for raw in raw_devices]
