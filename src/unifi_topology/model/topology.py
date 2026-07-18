"""Topology data classes and type definitions.

This module contains the core data structures for representing network topology.
The data classes themselves live in ``_topology_types`` (a cycle-free module) and
are re-exported here for public use.

For functions, see:
- classify: Device/client type classification
- edges: Edge building and topology construction
- clients: Client handling
- wan: WAN interface extraction
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ._topology_types import (  # noqa: F401
    ClientPortMap,
    Device,
    DeviceSource,
    Edge,
    PoeMap,
    PortInfo,
    PortMap,
    SpeedMap,
    TopologyResult,
    UplinkInfo,
    VlanMap,
    VpnTunnel,
    WanInfo,
    WanInterface,
)
from .helpers import normalize_mac

if TYPE_CHECKING:
    from .diff import TopologyDiff


def build_device_index(devices: Iterable[Device]) -> dict[str, str]:
    """Build MAC to name index for devices."""
    index: dict[str, str] = {}
    for device in devices:
        index[normalize_mac(device.mac)] = device.name
    return index


def _client_matches_mode(client: object, mode: str) -> bool:
    from ._client_access import _client_is_wired

    if mode == "all":
        return True
    wired = _client_is_wired(client)
    return not wired if mode == "wireless" else wired


def _client_name_entry(client: object) -> tuple[str, str] | None:
    from ._client_access import client_node_id
    from .classify import client_display_name

    node_id = client_node_id(client)
    if not node_id:
        return None
    return node_id, client_display_name(client) or node_id


def _filtered_clients(
    clients: Iterable[object],
    client_mode: str,
    only_unifi: bool,
) -> Iterable[object]:
    from .classify import client_is_unifi

    for client in clients:
        if not _client_matches_mode(client, client_mode):
            continue
        if only_unifi and not client_is_unifi(client):
            continue
        yield client


def _client_node_names(
    clients: Iterable[object],
    *,
    client_mode: str,
    only_unifi: bool,
) -> dict[str, str]:
    names: dict[str, str] = {}
    for client in _filtered_clients(clients, client_mode, only_unifi):
        entry = _client_name_entry(client)
        if entry:
            names[entry[0]] = entry[1]
    return names


def build_node_names(
    devices: Iterable[Device],
    clients: Iterable[object] | None = None,
    *,
    client_mode: str = "wired",
    only_unifi: bool = False,
) -> dict[str, str]:
    """Build a map of node IDs (MACs) to display names.

    Combines device and client name mappings into a single lookup.
    Device keys are ``normalize_mac(device.mac)``, client keys are
    ``normalize_mac(client["mac"])``.
    """
    names = build_device_index(devices)
    if clients:
        names.update(_client_node_names(clients, client_mode=client_mode, only_unifi=only_unifi))
    return names


# --- Topology class for serialization and diff ---


# Snapshot schema version. Bump when the serialized shape or node-id scheme
# changes so that from_dict can refuse snapshots it cannot interpret.
_SNAPSHOT_VERSION = 1


def _check_snapshot_version(version: object) -> None:
    if not isinstance(version, int) or version > _SNAPSHOT_VERSION:
        raise ValueError(
            f"Unsupported snapshot version: {version!r} "
            f"(this library supports up to {_SNAPSHOT_VERSION})"
        )


@dataclass
class Topology:
    """A complete network topology snapshot for serialization and comparison."""

    devices: list[Device] = field(default_factory=list)
    clients: list[dict[str, object]] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    timestamp: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize topology to a JSON-compatible dictionary."""
        from .snapshot import client_to_dict, device_to_dict, edge_to_dict

        return {
            "version": _SNAPSHOT_VERSION,
            "timestamp": self.timestamp,
            "devices": [device_to_dict(d) for d in self.devices],
            "clients": [client_to_dict(c) for c in self.clients],  # type: ignore[arg-type]
            "edges": [edge_to_dict(e) for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Topology:
        """Deserialize topology from a dictionary."""
        from .snapshot import client_from_dict, device_from_dict, edge_from_dict

        _check_snapshot_version(data.get("version", _SNAPSHOT_VERSION))

        devices_data = data.get("devices", [])
        clients_data = data.get("clients", [])
        edges_data = data.get("edges", [])

        devices = [device_from_dict(d) for d in devices_data]  # type: ignore[arg-type]
        clients = [client_from_dict(c) for c in clients_data]  # type: ignore[arg-type]
        edges = [edge_from_dict(e) for e in edges_data]  # type: ignore[arg-type]

        timestamp = data.get("timestamp")
        return cls(
            devices=devices,
            clients=clients,
            edges=edges,
            timestamp=timestamp if isinstance(timestamp, str) else None,
        )

    def diff(self, other: Topology) -> TopologyDiff:
        """Compare this topology with another and return differences."""
        from .diff import compare_topologies

        return compare_topologies(
            old_devices=self.devices,
            new_devices=other.devices,
            old_clients=self.clients,  # type: ignore[arg-type]
            new_clients=other.clients,  # type: ignore[arg-type]
            old_edges=self.edges,
            new_edges=other.edges,
            old_timestamp=self.timestamp,
            new_timestamp=other.timestamp,
        )


__all__ = [
    # Data classes
    "Device",
    "Edge",
    "PortInfo",
    "TopologyResult",
    "Topology",
    "UplinkInfo",
    "VpnTunnel",
    "WanInfo",
    "WanInterface",
    # Type aliases
    "ClientPortMap",
    "DeviceSource",
    "PoeMap",
    "PortMap",
    "SpeedMap",
    "VlanMap",
    # Functions
    "build_device_index",
    "build_node_names",
]
