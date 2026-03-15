"""Private helpers for coercing raw device records into typed devices."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from . import _topology_port_coerce
from ._raw import RawRecord
from .helpers import as_list, get_field
from .lldp import coerce_lldp
from .topology import Device, DeviceSource, UplinkInfo

logger = logging.getLogger(__name__)


def _extract_uplink_fields(value: object) -> tuple[object, object, object]:
    """Extract mac, name, and port from uplink data (dict or object)."""
    record = RawRecord(value)
    return (
        record.first("uplink_mac", "uplink_device_mac"),
        record.first("uplink_device_name", "uplink_name"),
        record.first("uplink_remote_port", "port_idx"),
    )


def _coerce_uplink_string(value: object) -> str | None:
    """Coerce a value to a stripped string or None."""
    return str(value).strip() if isinstance(value, str) and value.strip() else None


def _parse_uplink(value: object | None) -> UplinkInfo | None:
    if value is None:
        return None
    mac, name, port_raw = _extract_uplink_fields(value)
    mac_value = _coerce_uplink_string(mac)
    name_value = _coerce_uplink_string(name)
    port = _topology_port_coerce._as_int(port_raw)
    if mac_value is None and name_value is None and port is None:
        return None
    return UplinkInfo(mac=mac_value, name=name_value, port=port)


def _uplink_record(
    *,
    mac: object | None = None,
    name: object | None = None,
    port: object | None = None,
) -> dict[str, object | None]:
    return {
        "uplink_mac": mac,
        "uplink_device_name": name,
        "uplink_remote_port": port,
    }


def _uplink_info(device: DeviceSource) -> tuple[UplinkInfo | None, UplinkInfo | None]:
    uplink = _parse_uplink(get_field(device, "uplink"))
    last_uplink = _parse_uplink(get_field(device, "last_uplink"))

    if uplink is None:
        uplink = _parse_uplink(
            _uplink_record(
                mac=get_field(device, "uplink_mac") or get_field(device, "uplink_device_mac"),
                name=get_field(device, "uplink_device_name"),
                port=_topology_port_coerce._as_int(get_field(device, "uplink_remote_port")),
            )
        )

    if last_uplink is None:
        last_uplink = _parse_uplink(_uplink_record(mac=get_field(device, "last_uplink_mac")))

    return uplink, last_uplink


def _get_model_display_name(device: DeviceSource) -> str | None:
    """Extract the human-readable model name from device data."""
    return RawRecord(device).text("model_in_lts", "model_in_eol", "shortname", "model_name")


def _device_display_fields(
    device: DeviceSource,
) -> tuple[object | None, object | None, object | None, object | None, object | None]:
    record = RawRecord(device)
    return (
        _get_model_display_name(device) or record.get("model"),
        record.get("model"),
        record.first("ip", "ip_address"),
        record.first("type", "device_type"),
        record.first("displayable_version", "version"),
    )


def _gateway_mode(device: DeviceSource) -> bool | None:
    raw_gw_mode = RawRecord(device).get("in_gateway_mode")
    return raw_gw_mode if isinstance(raw_gw_mode, bool) else None


def _get_lldp_info(device: DeviceSource) -> object | None:
    """Try multiple field names to get LLDP info from device."""
    for field_name in ("lldp_info", "lldp", "lldp_table"):
        lldp = get_field(device, field_name)
        if lldp is not None:
            return lldp
    return None


def _resolve_lldp_info(
    device: DeviceSource,
    name: object,
    uplink: UplinkInfo | None,
    last_uplink: UplinkInfo | None,
) -> list[object]:
    """Resolve LLDP info, falling back to empty list if uplink exists."""
    lldp_info = _get_lldp_info(device)
    if lldp_info is not None:
        return as_list(lldp_info)
    if uplink or last_uplink:
        logger.warning("Device %s missing LLDP info; using uplink fallback", name)
        return []
    raise ValueError(f"Device {name} missing LLDP info")


def _device_identity(device: DeviceSource) -> tuple[str, str]:
    record = RawRecord(device)
    name = record.get("name")
    mac = record.get("mac")
    if not name or not mac:
        raise ValueError("Device missing name or mac")
    return str(name), str(mac)


def coerce_device(device: DeviceSource, network_vlan_map: dict[str, int] | None = None) -> Device:
    name, mac = _device_identity(device)
    model_name, model, ip, dev_type, version = _device_display_fields(device)
    in_gateway_mode = _gateway_mode(device)

    uplink, last_uplink = _uplink_info(device)
    coerced_lldp = [
        coerce_lldp(entry)
        for entry in _resolve_lldp_info(device, name, uplink, last_uplink)
    ]

    return Device(
        name=name,
        model_name=str(model_name or ""),
        model=str(model or ""),
        mac=mac,
        ip=str(ip or ""),
        type=str(dev_type or ""),
        lldp_info=coerced_lldp,
        port_table=_topology_port_coerce._coerce_port_table(device, network_vlan_map),
        poe_ports=_topology_port_coerce._poe_ports_from_device(device, network_vlan_map),
        uplink=uplink,
        last_uplink=last_uplink,
        version=str(version or ""),
        in_gateway_mode=in_gateway_mode,
        network_table=_topology_port_coerce._coerce_network_table(device),
    )


def normalize_devices(
    devices: Iterable[DeviceSource], network_vlan_map: dict[str, int] | None = None
) -> list[Device]:
    """Coerce raw device dicts/objects into typed :class:`Device` instances."""
    return [coerce_device(device, network_vlan_map) for device in devices]
