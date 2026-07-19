"""Per-entity describers, property extractors, keys, and comparison specs."""

from __future__ import annotations

from collections.abc import Hashable
from typing import Any

from ._diff_engine import EntityCompareSpec, _single_change
from ._topology_types import Device, Edge
from .helpers import normalize_mac
from .snapshot import device_to_dict, edge_to_dict

# --- Device ---


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


def _device_key(device: Device) -> Hashable | None:
    return normalize_mac(device.mac) if device.mac else None


# --- Client ---


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


def _client_key(client: dict[str, Any]) -> Hashable | None:
    mac = client.get("mac")
    return normalize_mac(mac) if mac else None


def _client_name(client: dict[str, Any]) -> str | None:
    return client.get("name") or client.get("hostname")


# --- Edge ---


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


# --- Comparison specs ---


_DEVICE_SPEC: EntityCompareSpec[Device] = EntityCompareSpec(
    entity_type="device",
    event_prefix="node",
    key=_device_key,
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
