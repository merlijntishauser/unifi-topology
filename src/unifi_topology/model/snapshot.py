"""Serialization helpers for topology data structures.

Provides to_dict/from_dict conversions for persistence and transmission.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields, is_dataclass
from typing import Any, TypeVar

from ._topology_types import Device, Edge, PortInfo, UplinkInfo, WanInfo, WanInterface
from .connection import ConnectionInfo
from .lldp import LLDPEntry

T = TypeVar("T")
_JSON_SCALARS = (str, int, float, bool)
_CLIENT_RELEVANT_KEYS = frozenset(
    {
        "mac",
        "name",
        "hostname",
        "ip",
        "vlan",
        "vlan_id",
        "is_wired",
        "is_unifi",
        "is_unifi_device",
        "ap_mac",
        "sw_mac",
        "uplink_mac",
        "uplink_device_mac",
        "sw_port",
        "uplink_remote_port",
        "channel",
        "signal",
        "noise",
        "tx_rate",
        "rx_rate",
        "satisfaction",
        "oui",
        "vendor",
        "unifi_device_info_from_ucore",
    }
)


def _serialize_sequence(values: tuple[Any, ...] | list[Any]) -> list[Any]:
    return [_serialize_value(value) for value in values]


def _serialize_mapping(values: dict[Any, Any]) -> dict[Any, Any]:
    return {key: _serialize_value(value) for key, value in values.items()}


def _scalar_or_none(value: Any) -> Any:
    if value is None or isinstance(value, _JSON_SCALARS):
        return value
    return _UNSERIALIZED


def _serialize_collection(value: Any) -> Any:
    if isinstance(value, tuple | list):
        return _serialize_sequence(value)
    if isinstance(value, dict):
        return _serialize_mapping(value)
    return _UNSERIALIZED


def _is_dataclass_instance(value: Any) -> bool:
    return is_dataclass(value) and not isinstance(value, type)


_UNSERIALIZED = object()


def _serialize_value(value: Any) -> Any:
    """Recursively serialize a value to JSON-compatible form."""
    scalar = _scalar_or_none(value)
    if scalar is not _UNSERIALIZED:
        return scalar
    collection = _serialize_collection(value)
    if collection is not _UNSERIALIZED:
        return collection
    if _is_dataclass_instance(value):
        return _dataclass_to_dict(value)
    return str(value)


def _dataclass_to_dict(obj: Any) -> dict[str, Any]:
    """Convert a dataclass instance to a dictionary."""
    result: dict[str, Any] = {}
    for field in fields(obj):
        value = getattr(obj, field.name)
        result[field.name] = _serialize_value(value)
    return result


def _optional_to_dict[T](
    value: T | None,
    serializer: Callable[[T], dict[str, Any]],
) -> dict[str, Any] | None:
    if value is None:
        return None
    return serializer(value)


def _optional_from_dict[T](
    data: dict[str, Any],
    key: str,
    loader: Callable[[dict[str, Any]], T],
) -> T | None:
    value = data.get(key)
    if not isinstance(value, dict):
        return None
    return loader(value)


def _typed_list[T](
    data: dict[str, Any],
    key: str,
    loader: Callable[[dict[str, Any]], T],
) -> list[T]:
    values = data.get(key, [])
    if not isinstance(values, list):
        return []
    return [loader(value) for value in values if isinstance(value, dict)]


def _poe_ports_to_dict(poe_ports: dict[int, bool]) -> dict[str, bool]:
    return {str(key): value for key, value in poe_ports.items()}


def _poe_ports_from_dict(data: dict[str, Any]) -> dict[int, bool]:
    values = data.get("poe_ports", {})
    if not isinstance(values, dict):
        return {}
    result: dict[int, bool] = {}
    for key, value in values.items():
        try:
            result[int(key)] = bool(value)
        except (TypeError, ValueError):
            continue
    return result


def _network_table_from_dict(data: dict[str, Any]) -> list[dict[str, Any]]:
    network_table = data.get("network_table", [])
    if not isinstance(network_table, list):
        return []
    return [entry for entry in network_table if isinstance(entry, dict)]


def _device_base_dict(device: Device) -> dict[str, Any]:
    return {
        "name": device.name,
        "model_name": device.model_name,
        "model": device.model,
        "mac": device.mac,
        "ip": device.ip,
        "type": device.type,
        "lldp_info": [lldp_entry_to_dict(entry) for entry in device.lldp_info],
        "port_table": [port_info_to_dict(port) for port in device.port_table],
        "poe_ports": _poe_ports_to_dict(device.poe_ports),
        "uplink": _optional_to_dict(device.uplink, uplink_info_to_dict),
        "last_uplink": _optional_to_dict(device.last_uplink, uplink_info_to_dict),
        "version": device.version,
    }


def _edge_connection_to_dict(edge: Edge) -> dict[str, Any] | None:
    return _optional_to_dict(edge.connection, connection_info_to_dict)


# --- PortInfo ---


def port_info_to_dict(port: PortInfo) -> dict[str, Any]:
    """Serialize a PortInfo to a dictionary."""
    return _dataclass_to_dict(port)


def port_info_from_dict(data: dict[str, Any]) -> PortInfo:
    """Deserialize a PortInfo from a dictionary."""
    return PortInfo(
        port_idx=data.get("port_idx"),
        name=data.get("name"),
        ifname=data.get("ifname"),
        speed=data.get("speed"),
        aggregation_group=data.get("aggregation_group"),
        port_poe=data.get("port_poe", False),
        poe_enable=data.get("poe_enable", False),
        poe_good=data.get("poe_good", False),
        poe_power=data.get("poe_power"),
        up=data.get("up"),
        native_vlan=data.get("native_vlan"),
        tagged_vlans=tuple(data.get("tagged_vlans", [])),
        wan_networkconf_id=data.get("wan_networkconf_id"),
    )


# --- UplinkInfo ---


def uplink_info_to_dict(uplink: UplinkInfo) -> dict[str, Any]:
    """Serialize an UplinkInfo to a dictionary."""
    return _dataclass_to_dict(uplink)


def uplink_info_from_dict(data: dict[str, Any]) -> UplinkInfo:
    """Deserialize an UplinkInfo from a dictionary."""
    return UplinkInfo(
        mac=data.get("mac"),
        name=data.get("name"),
        port=data.get("port"),
    )


# --- LLDPEntry ---


def lldp_entry_to_dict(entry: LLDPEntry) -> dict[str, Any]:
    """Serialize an LLDPEntry to a dictionary."""
    return _dataclass_to_dict(entry)


def lldp_entry_from_dict(data: dict[str, Any]) -> LLDPEntry:
    """Deserialize an LLDPEntry from a dictionary."""
    return LLDPEntry(
        chassis_id=data.get("chassis_id", ""),
        port_id=data.get("port_id", ""),
        port_desc=data.get("port_desc"),
        local_port_name=data.get("local_port_name"),
        local_port_idx=data.get("local_port_idx"),
    )


# --- WanInterface ---


def wan_interface_to_dict(wan: WanInterface) -> dict[str, Any]:
    """Serialize a WanInterface to a dictionary."""
    return _dataclass_to_dict(wan)


def wan_interface_from_dict(data: dict[str, Any]) -> WanInterface:
    """Deserialize a WanInterface from a dictionary."""
    return WanInterface(
        port_idx=data.get("port_idx", 0),
        link_speed=data.get("link_speed"),
        ip_address=data.get("ip_address"),
        enabled=data.get("enabled", False),
        label=data.get("label"),
        isp_speed=data.get("isp_speed"),
    )


# --- WanInfo ---


def wan_info_to_dict(wan_info: WanInfo) -> dict[str, Any]:
    """Serialize a WanInfo to a dictionary."""
    return {
        "wan1": _optional_to_dict(wan_info.wan1, wan_interface_to_dict),
        "wan2": _optional_to_dict(wan_info.wan2, wan_interface_to_dict),
    }


def wan_info_from_dict(data: dict[str, Any]) -> WanInfo:
    """Deserialize a WanInfo from a dictionary."""
    return WanInfo(
        wan1=_optional_from_dict(data, "wan1", wan_interface_from_dict),
        wan2=_optional_from_dict(data, "wan2", wan_interface_from_dict),
    )


# --- Device ---


def device_to_dict(device: Device) -> dict[str, Any]:
    """Serialize a Device to a dictionary."""
    result = _device_base_dict(device)
    if device.network_table:
        result["network_table"] = device.network_table
    return result


def device_from_dict(data: dict[str, Any]) -> Device:
    """Deserialize a Device from a dictionary."""
    return Device(
        name=data.get("name", ""),
        model_name=data.get("model_name", ""),
        model=data.get("model", ""),
        mac=data.get("mac", ""),
        ip=data.get("ip", ""),
        type=data.get("type", ""),
        lldp_info=_typed_list(data, "lldp_info", lldp_entry_from_dict),
        port_table=_typed_list(data, "port_table", port_info_from_dict),
        poe_ports=_poe_ports_from_dict(data),
        uplink=_optional_from_dict(data, "uplink", uplink_info_from_dict),
        last_uplink=_optional_from_dict(data, "last_uplink", uplink_info_from_dict),
        version=data.get("version", ""),
        network_table=_network_table_from_dict(data),
    )


# --- ConnectionInfo ---


def connection_info_to_dict(conn: ConnectionInfo) -> dict[str, Any]:
    """Serialize a ConnectionInfo to a dictionary."""
    return _dataclass_to_dict(conn)


def connection_info_from_dict(data: dict[str, Any]) -> ConnectionInfo:
    """Deserialize a ConnectionInfo from a dictionary."""
    return ConnectionInfo(
        signal_dbm=data.get("signal_dbm"),
        noise_dbm=data.get("noise_dbm"),
        tx_rate_mbps=data.get("tx_rate_mbps"),
        rx_rate_mbps=data.get("rx_rate_mbps"),
        satisfaction=data.get("satisfaction"),
        quality=data.get("quality"),
    )


# --- Edge ---


def edge_to_dict(edge: Edge) -> dict[str, Any]:
    """Serialize an Edge to a dictionary."""
    return {
        "left": edge.left,
        "right": edge.right,
        "label": edge.label,
        "poe": edge.poe,
        "wireless": edge.wireless,
        "speed": edge.speed,
        "channel": edge.channel,
        "vlans": list(edge.vlans),
        "active_vlans": list(edge.active_vlans),
        "is_trunk": edge.is_trunk,
        "connection": _edge_connection_to_dict(edge),
    }


def edge_from_dict(data: dict[str, Any]) -> Edge:
    """Deserialize an Edge from a dictionary."""
    return Edge(
        left=data.get("left", ""),
        right=data.get("right", ""),
        label=data.get("label"),
        poe=data.get("poe", False),
        wireless=data.get("wireless", False),
        speed=data.get("speed"),
        channel=data.get("channel"),
        vlans=tuple(data.get("vlans", [])),
        active_vlans=tuple(data.get("active_vlans", [])),
        is_trunk=data.get("is_trunk", False),
        connection=_optional_from_dict(data, "connection", connection_info_from_dict),
    )


# --- Client (dict-based, since clients come from API as dicts) ---


def client_to_dict(client: dict[str, Any]) -> dict[str, Any]:
    """Serialize a client dict, keeping only relevant fields."""
    return {key: value for key, value in client.items() if key in _CLIENT_RELEVANT_KEYS}


def client_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize a client dict (identity for now, but validates structure)."""
    return dict(data)
