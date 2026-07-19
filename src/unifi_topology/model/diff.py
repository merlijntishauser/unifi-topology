"""Topology comparison and change detection.

Provides functions to compare two topology snapshots and generate structured
change events for integration with monitoring systems like Home Assistant.

The implementation is split across three private modules:
- ``_diff_events``: the ``TopologyChangeEvent`` / ``TopologyDiff`` types and summary.
- ``_diff_engine``: the generic ``EntityCompareSpec`` comparison machinery.
- ``_diff_specs``: per-entity describers, property extractors, and specs.

This module is the thin public facade.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ._diff_engine import _compare_entities, _compare_optional_entities
from ._diff_events import TopologyChangeEvent, TopologyDiff, _build_summary
from ._diff_specs import (
    _CLIENT_SPEC,
    _DEVICE_SPEC,
    _EDGE_SPEC,
    _client_uplink_port_value,
    _client_vlan_value,
    _device_key,
)
from ._topology_types import Device, Edge

__all__ = [
    "TopologyChangeEvent",
    "TopologyDiff",
    "compare_topologies",
    # Re-exported for tests that characterize the comparison internals.
    "_client_uplink_port_value",
    "_client_vlan_value",
    "_device_key",
]


def compare_topologies(
    old_devices: list[Device],
    new_devices: list[Device],
    old_clients: list[dict[str, Any]] | None = None,
    new_clients: list[dict[str, Any]] | None = None,
    old_edges: list[Edge] | None = None,
    new_edges: list[Edge] | None = None,
    *,
    old_timestamp: str | None = None,
    new_timestamp: str | None = None,
) -> TopologyDiff:
    """Compare two topology snapshots and return structured change events.

    Args:
        old_devices: Devices from the previous snapshot.
        new_devices: Devices from the current snapshot.
        old_clients: Clients from the previous snapshot (optional).
        new_clients: Clients from the current snapshot (optional).
        old_edges: Edges from the previous snapshot (optional).
        new_edges: Edges from the current snapshot (optional).
        old_timestamp: ISO timestamp of old snapshot.
        new_timestamp: ISO timestamp of new snapshot.

    Returns:
        TopologyDiff containing all detected changes.
    """
    events: list[TopologyChangeEvent] = []
    timestamp = new_timestamp or datetime.now(UTC).isoformat()

    _compare_entities(old_devices, new_devices, _DEVICE_SPEC, events, timestamp)
    _compare_optional_entities(old_clients, new_clients, _CLIENT_SPEC, events, timestamp)
    _compare_optional_entities(old_edges, new_edges, _EDGE_SPEC, events, timestamp)

    return TopologyDiff(
        events=events,
        old_timestamp=old_timestamp,
        new_timestamp=new_timestamp,
        summary=_build_summary(events),
    )
