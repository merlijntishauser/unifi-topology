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
    general = raw.get("general_temperature")
    if general is not None:
        try:
            return float(general)
        except (TypeError, ValueError):
            pass
    sys_stats = raw.get("system-stats", {})
    temps = sys_stats.get("temps") if isinstance(sys_stats, dict) else None
    if isinstance(temps, dict) and temps:
        first_value = next(iter(temps.values()))
        try:
            return float(first_value)
        except (TypeError, ValueError):
            pass
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


def normalize_device_stats(raw_devices: Iterable[dict[str, Any]]) -> list[DeviceStats]:
    """Normalize raw device dicts from the UniFi API to DeviceStats dataclasses.

    Accepts the output of ``fetch_device_stats()`` and extracts CPU, memory,
    temperature, traffic counters, uptime, PoE port draw, and budget into
    typed ``DeviceStats`` objects.  Device types are normalized (ugw/udm to
    gateway, usw to switch, uap to ap).
    """
    stats: list[DeviceStats] = []
    for raw in raw_devices:
        system_stats = raw.get("system-stats", {})
        if not isinstance(system_stats, dict):
            system_stats = {}
        tx_bytes = raw.get("tx_bytes")
        if tx_bytes is None:
            tx_bytes = raw.get("stat", {}).get("tx_bytes", 0)
        rx_bytes = raw.get("rx_bytes")
        if rx_bytes is None:
            rx_bytes = raw.get("stat", {}).get("rx_bytes", 0)
        poe_budget_raw = raw.get("total_max_power")
        stats.append(
            DeviceStats(
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
                poe_budget=_as_float(poe_budget_raw) if poe_budget_raw is not None else None,
            )
        )
    return stats
