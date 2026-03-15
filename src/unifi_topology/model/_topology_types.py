"""Core topology data classes.

Standalone module with no imports from snapshot or diff, breaking the
cyclic dependency that existed when these types lived in topology.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .lldp import LLDPEntry

if TYPE_CHECKING:
    from .connection import ConnectionInfo


@dataclass(frozen=True)
class UplinkInfo:
    """Information about a device's uplink connection."""

    mac: str | None
    name: str | None
    port: int | None


@dataclass(frozen=True)
class PortInfo:
    """Information about a switch/gateway port."""

    port_idx: int | None
    name: str | None
    ifname: str | None
    speed: int | None
    aggregation_group: str | None
    port_poe: bool
    poe_enable: bool
    poe_good: bool
    poe_power: float | None
    up: bool | None = None
    native_vlan: int | None = None
    tagged_vlans: tuple[int, ...] = ()
    wan_networkconf_id: str | None = None


@dataclass(frozen=True)
class Device:
    """A network device (gateway, switch, or access point)."""

    name: str
    model_name: str
    model: str
    mac: str
    ip: str
    type: str
    lldp_info: list[LLDPEntry]
    port_table: list[PortInfo] = field(default_factory=list)
    poe_ports: dict[int, bool] = field(default_factory=dict)
    uplink: UplinkInfo | None = None
    last_uplink: UplinkInfo | None = None
    version: str = ""
    in_gateway_mode: bool | None = None
    network_table: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class Edge:
    """A connection between two nodes in the topology."""

    left: str
    right: str
    label: str | None = None
    poe: bool = False
    wireless: bool = False
    speed: int | None = None
    channel: int | None = None
    vlans: tuple[int, ...] = ()
    active_vlans: tuple[int, ...] = ()
    is_trunk: bool = False
    connection: ConnectionInfo | None = None


@dataclass(frozen=True)
class WanInterface:
    """Information about a WAN interface on a gateway."""

    port_idx: int
    link_speed: int | None
    ip_address: str | None
    enabled: bool
    label: str | None = None
    isp_speed: str | None = None


@dataclass(frozen=True)
class WanInfo:
    """WAN interface information for a gateway device."""

    wan1: WanInterface | None = None
    wan2: WanInterface | None = None


@dataclass(frozen=True)
class VpnTunnel:
    """A single VPN tunnel on a gateway device."""

    name: str
    vpn_type: str
    remote_subnets: tuple[str, ...]
    ifname: str | None
    enabled: bool
    up: bool
    gateway_mac: str | None


@dataclass(frozen=True)
class TopologyResult:
    """Result of building a topology."""

    raw_edges: list[Edge]
    tree_edges: list[Edge]


# Type aliases for maps used in edge building
type DeviceSource = object
type PortMap = dict[tuple[str, str], str]
type PoeMap = dict[tuple[str, str], bool]
type SpeedMap = dict[tuple[str, str], int]
type ClientPortMap = dict[str, list[tuple[int, str]]]
type VlanMap = dict[tuple[str, str], tuple[int, ...]]
