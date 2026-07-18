"""Topology comparison and change detection.

Provides functions to compare two topology snapshots and generate structured
change events for integration with monitoring systems like Home Assistant.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ._topology_types import Device, Edge
from .helpers import normalize_mac
from .snapshot import device_to_dict, edge_to_dict


@dataclass
class TopologyChangeEvent:
    """A single change detected between two topology snapshots."""

    event_type: str
    """One of: node_added, node_removed, node_changed, edge_added, edge_removed, edge_changed"""

    entity_type: str
    """'device', 'client', or 'edge'"""

    identifier: str
    """MAC address - stable identifier across renames"""

    name: str | None
    """Human-readable name (from newer topology if changed)"""

    description: str
    """Human-readable message for notifications"""

    details: dict[str, Any] = field(default_factory=dict)
    """Event-specific payload"""

    timestamp: str | None = None
    """ISO timestamp if available"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "identifier": self.identifier,
            "name": self.name,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class TopologyDiff:
    """Result of comparing two topology snapshots."""

    events: list[TopologyChangeEvent] = field(default_factory=list)
    """All detected changes"""

    old_timestamp: str | None = None
    """Timestamp from old topology metadata"""

    new_timestamp: str | None = None
    """Timestamp from new topology metadata"""

    summary: str = ""
    """Human-readable summary like '3 devices added, 1 removed'"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "events": [e.to_dict() for e in self.events],
            "old_timestamp": self.old_timestamp,
            "new_timestamp": self.new_timestamp,
            "summary": self.summary,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def filter(
        self,
        event_types: set[str] | None = None,
        entity_types: set[str] | None = None,
    ) -> TopologyDiff:
        """Return filtered diff with only matching events."""
        filtered = [
            event
            for event in self.events
            if _event_matches(event, event_types=event_types, entity_types=entity_types)
        ]
        return TopologyDiff(
            events=filtered,
            old_timestamp=self.old_timestamp,
            new_timestamp=self.new_timestamp,
            summary=_build_summary(filtered),
        )


def _event_matches(
    event: TopologyChangeEvent,
    *,
    event_types: set[str] | None,
    entity_types: set[str] | None,
) -> bool:
    if event_types is not None and event.event_type not in event_types:
        return False
    if entity_types is not None and event.entity_type not in entity_types:
        return False
    return True


def _pluralize(count: int, singular: str) -> str:
    """Return 'N item' or 'N items' based on count."""
    return f"{count} {singular}{'s' if count != 1 else ''}"


def _add_count_part(parts: list[str], count: int, noun: str, verb: str) -> None:
    """Add a count part to the summary list if count > 0."""
    if count:
        parts.append(f"{_pluralize(count, noun)} {verb}")


def _build_summary(events: list[TopologyChangeEvent]) -> str:
    """Build a human-readable summary of changes."""
    counts: dict[str, int] = {}
    for event in events:
        key = f"{event.entity_type}_{event.event_type}"
        counts[key] = counts.get(key, 0) + 1

    parts: list[str] = []

    # Devices
    _add_count_part(parts, counts.get("device_node_added", 0), "device", "added")
    _add_count_part(parts, counts.get("device_node_removed", 0), "device", "removed")
    _add_count_part(parts, counts.get("device_node_changed", 0), "device", "changed")

    # Clients
    _add_count_part(parts, counts.get("client_node_added", 0), "client", "added")
    _add_count_part(parts, counts.get("client_node_removed", 0), "client", "removed")
    _add_count_part(parts, counts.get("client_node_changed", 0), "client", "changed")

    # Edges
    _add_count_part(parts, counts.get("edge_edge_added", 0), "connection", "added")
    _add_count_part(parts, counts.get("edge_edge_removed", 0), "connection", "removed")
    _add_count_part(parts, counts.get("edge_edge_changed", 0), "connection", "changed")

    return ", ".join(parts) if parts else "No changes"


# --- Node comparison ---


def _device_properties(device: Device) -> dict[str, Any]:
    """Extract comparable properties from a device."""
    return {
        "name": device.name,
        "model": device.model,
        "model_name": device.model_name,
        "ip": device.ip,
        "type": device.type,
        "version": device.version,
        "uplink_mac": device.uplink.mac if device.uplink else None,
        "uplink_port": device.uplink.port if device.uplink else None,
    }


def _client_name_value(client: dict[str, Any]) -> Any:
    return client.get("name") or client.get("hostname")


def _first_present(client: dict[str, Any], *keys: str) -> Any:
    """Return the first value whose key is present and not None.

    Uses ``is not None`` rather than truthiness so that a legitimate 0 (VLAN 0,
    port 0) is not skipped in favour of a later, unrelated key.
    """
    for key in keys:
        value = client.get(key)
        if value is not None:
            return value
    return None


def _client_vlan_value(client: dict[str, Any]) -> Any:
    return _first_present(client, "vlan", "vlan_id")


def _client_uplink_mac_value(client: dict[str, Any]) -> Any:
    return _first_present(client, "ap_mac", "sw_mac", "uplink_mac")


def _client_uplink_port_value(client: dict[str, Any]) -> Any:
    return _first_present(client, "sw_port", "uplink_remote_port")


def _client_properties(client: dict[str, Any]) -> dict[str, Any]:
    """Extract comparable properties from a client."""
    return {
        "name": _client_name_value(client),
        "ip": client.get("ip"),
        "vlan": _client_vlan_value(client),
        "is_wired": client.get("is_wired"),
        "uplink_mac": _client_uplink_mac_value(client),
        "uplink_port": _client_uplink_port_value(client),
        "channel": client.get("channel"),
        # signal/satisfaction are intentionally excluded: they fluctuate every
        # poll and would emit a client_node_changed event on nearly every diff.
    }


def _compare_properties(
    old_props: dict[str, Any],
    new_props: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Compare two property dicts and return changes."""
    changes: dict[str, dict[str, Any]] = {}
    all_keys = set(old_props.keys()) | set(new_props.keys())
    for key in all_keys:
        old_val = old_props.get(key)
        new_val = new_props.get(key)
        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}
    return changes


def _single_change(
    changes: dict[str, dict[str, Any]],
) -> tuple[str, Any, Any] | None:
    if len(changes) != 1:
        return None
    key, values = next(iter(changes.items()))
    return key, values.get("old"), values.get("new")


@dataclass(frozen=True)
class EntityCompareSpec[T]:
    """Specification for comparing a particular entity type."""

    entity_type: str
    event_prefix: str
    key: Callable[[T], Hashable | None]
    sort_key: Callable[[Any], Any]
    name: Callable[[T], str | None]
    identifier: Callable[[T, Hashable], str]
    properties: Callable[[T], dict[str, Any]]
    serialize: Callable[[T], dict[str, Any]]
    describe_added: Callable[[T], str]
    describe_removed: Callable[[T], str]
    describe_changed: Callable[[T, dict[str, dict[str, Any]]], str]


def _build_entity_map[T](
    items: list[T], key_fn: Callable[[T], Hashable | None]
) -> dict[Hashable, T]:
    """Build a lookup map from items, skipping any whose key is None."""
    return {k: item for item in items if (k := key_fn(item)) is not None}


def _compare_entities[T](
    old_items: list[T],
    new_items: list[T],
    spec: EntityCompareSpec[T],
    events: list[TopologyChangeEvent],
    timestamp: str,
) -> None:
    """Compare two entity lists and emit change events."""
    old_map = _build_entity_map(old_items, spec.key)
    new_map = _build_entity_map(new_items, spec.key)
    old_keys = set(old_map)
    new_keys = set(new_map)

    for key in sorted(new_keys - old_keys, key=spec.sort_key):
        item = new_map[key]
        events.append(
            TopologyChangeEvent(
                event_type=f"{spec.event_prefix}_added",
                entity_type=spec.entity_type,
                identifier=spec.identifier(item, key),
                name=spec.name(item),
                description=spec.describe_added(item),
                details=spec.serialize(item),
                timestamp=timestamp,
            )
        )

    for key in sorted(old_keys - new_keys, key=spec.sort_key):
        item = old_map[key]
        events.append(
            TopologyChangeEvent(
                event_type=f"{spec.event_prefix}_removed",
                entity_type=spec.entity_type,
                identifier=spec.identifier(item, key),
                name=spec.name(item),
                description=spec.describe_removed(item),
                details=spec.serialize(item),
                timestamp=timestamp,
            )
        )

    for key in sorted(old_keys & new_keys, key=spec.sort_key):
        new_item = new_map[key]
        changes = _compare_properties(spec.properties(old_map[key]), spec.properties(new_item))
        if changes:
            events.append(
                TopologyChangeEvent(
                    event_type=f"{spec.event_prefix}_changed",
                    entity_type=spec.entity_type,
                    identifier=spec.identifier(new_item, key),
                    name=spec.name(new_item),
                    description=spec.describe_changed(new_item, changes),
                    details={"changes": changes},
                    timestamp=timestamp,
                )
            )


# --- Node comparison ---


def _describe_device_added(device: Device) -> str:
    """Generate description for device added event."""
    return f"Device '{device.name}' appeared on network"


def _describe_device_removed(device: Device) -> str:
    """Generate description for device removed event."""
    return f"Device '{device.name}' disappeared from network"


def _device_single_change_description(
    device: Device,
    change: tuple[str, Any, Any],
) -> str:
    key, old_val, new_val = change
    if key == "ip":
        return f"Device '{device.name}' IP changed from {old_val} to {new_val}"
    if key == "name":
        return f"Device renamed from '{old_val}' to '{new_val}'"
    if key == "uplink_mac":
        return f"Device '{device.name}' uplink changed"
    if key == "uplink_port":
        return f"Device '{device.name}' moved to port {new_val}"
    return f"Device '{device.name}' {key} changed"


def _describe_device_changed(device: Device, changes: dict[str, dict[str, Any]]) -> str:
    """Generate description for device changed event."""
    change = _single_change(changes)
    if change is not None:
        return _device_single_change_description(device, change)
    return f"Device '{device.name}' changed ({len(changes)} properties)"


def _client_display_name(client: dict[str, Any]) -> str:
    return client.get("name") or client.get("hostname") or client.get("mac", "unknown")


def _describe_client_added(client: dict[str, Any]) -> str:
    """Generate description for client added event."""
    name = _client_display_name(client)
    is_wired = client.get("is_wired", True)
    conn_type = "wired" if is_wired else "WiFi"
    return f"Client '{name}' connected via {conn_type}"


def _describe_client_removed(client: dict[str, Any]) -> str:
    """Generate description for client removed event."""
    return f"Client '{_client_display_name(client)}' disconnected"


def _client_single_change_description(
    name: str,
    change: tuple[str, Any, Any],
) -> str:
    key, old_val, new_val = change
    if key == "vlan":
        return f"Client '{name}' changed VLAN from {old_val} to {new_val}"
    if key == "ip":
        return f"Client '{name}' IP changed from {old_val} to {new_val}"
    if key == "uplink_mac":
        return f"Client '{name}' moved to different device"
    if key == "uplink_port":
        return f"Client '{name}' moved to port {new_val}"
    return f"Client '{name}' {key} changed"


def _describe_client_changed(client: dict[str, Any], changes: dict[str, dict[str, Any]]) -> str:
    """Generate description for client changed event."""
    name = _client_display_name(client)
    change = _single_change(changes)
    if change is not None:
        return _client_single_change_description(name, change)
    return f"Client '{name}' changed ({len(changes)} properties)"


# --- Edge comparison ---


def _edge_key(edge: Edge) -> frozenset[str]:
    """Create a stable key for an edge (order-independent)."""
    return frozenset({edge.left, edge.right})


def _edge_properties(edge: Edge) -> dict[str, Any]:
    """Extract comparable properties from an edge."""
    return {
        "label": edge.label,
        "poe": edge.poe,
        "wireless": edge.wireless,
        "speed": edge.speed,
        "channel": edge.channel,
        "vlans": edge.vlans,
        "is_trunk": edge.is_trunk,
    }


def _describe_edge_added(edge: Edge) -> str:
    """Generate description for edge added event."""
    conn_type = "wireless" if edge.wireless else "wired"
    return f"Connection added: {edge.left} <-> {edge.right} ({conn_type})"


def _describe_edge_removed(edge: Edge) -> str:
    """Generate description for edge removed event."""
    return f"Connection removed: {edge.left} <-> {edge.right}"


def _describe_edge_changed(edge: Edge, changes: dict[str, dict[str, Any]]) -> str:
    """Generate description for edge changed event."""
    change = _single_change(changes)
    if change is not None:
        key, old_val, new_val = change
        if key == "speed":
            return (
                f"Connection {edge.left} <-> {edge.right} speed changed from {old_val} to {new_val}"
            )
        if key == "poe":
            poe_state = "enabled" if new_val else "disabled"
            return f"Connection {edge.left} <-> {edge.right} PoE {poe_state}"
    return f"Connection {edge.left} <-> {edge.right} changed"


# --- Entity comparison specs ---


def _client_key(client: dict[str, Any]) -> Hashable | None:
    mac = client.get("mac")
    return normalize_mac(mac) if mac else None


def _client_name(client: dict[str, Any]) -> str | None:
    return client.get("name") or client.get("hostname")


def _compare_optional_entities[T](
    old_items: list[T] | None,
    new_items: list[T] | None,
    spec: EntityCompareSpec[T],
    events: list[TopologyChangeEvent],
    timestamp: str,
) -> None:
    if old_items is None or new_items is None:
        return
    _compare_entities(old_items, new_items, spec, events, timestamp)


_DEVICE_SPEC: EntityCompareSpec[Device] = EntityCompareSpec(
    entity_type="device",
    event_prefix="node",
    key=lambda d: normalize_mac(d.mac),
    sort_key=lambda k: k,
    name=lambda d: d.name,
    identifier=lambda _d, k: str(k),
    properties=_device_properties,
    serialize=device_to_dict,
    describe_added=_describe_device_added,
    describe_removed=_describe_device_removed,
    describe_changed=_describe_device_changed,
)

_CLIENT_SPEC: EntityCompareSpec[dict[str, Any]] = EntityCompareSpec(
    entity_type="client",
    event_prefix="node",
    key=_client_key,
    sort_key=lambda k: k,
    name=_client_name,
    identifier=lambda _c, k: str(k),
    properties=_client_properties,
    serialize=_client_properties,
    describe_added=_describe_client_added,
    describe_removed=_describe_client_removed,
    describe_changed=_describe_client_changed,
)

_EDGE_SPEC: EntityCompareSpec[Edge] = EntityCompareSpec(
    entity_type="edge",
    event_prefix="edge",
    key=_edge_key,
    sort_key=lambda k: tuple(sorted(k)),
    name=lambda _e: None,
    identifier=lambda e, _k: f"{e.left}:{e.right}",
    properties=_edge_properties,
    serialize=edge_to_dict,
    describe_added=_describe_edge_added,
    describe_removed=_describe_edge_removed,
    describe_changed=_describe_edge_changed,
)


# --- Main comparison function ---


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
