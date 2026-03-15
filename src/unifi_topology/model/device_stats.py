"""Device statistics data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PoePortStats:
    """PoE statistics for a single switch port."""

    port_idx: int
    poe_power: float
    poe_mode: str


@dataclass(frozen=True)
class DeviceStats:
    """Runtime statistics for a UniFi device."""

    mac: str
    name: str
    model: str
    type: str
    uptime: int  # seconds
    cpu: float  # percentage 0-100
    mem: float  # percentage 0-100
    temperature: float | None = None  # celsius
    tx_bytes: int = 0
    rx_bytes: int = 0
    num_sta: int = 0
    version: str = ""
    poe_ports: list[PoePortStats] = field(default_factory=list)
    poe_budget: float | None = None  # watts (switches only)
