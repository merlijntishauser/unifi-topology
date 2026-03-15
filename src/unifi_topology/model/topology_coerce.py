"""Type coercion and device normalization utilities."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from ._raw import RawRecord
from .helpers import as_bool, as_list, get_field
from .lldp import coerce_lldp
from .topology import Device, DeviceSource, PortInfo, UplinkInfo

logger = logging.getLogger(__name__)


def _as_float(value: object | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _as_int(value: object | None) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _as_group_id(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return value.strip() or None
    return None


def _aggregation_group(port_entry: object) -> object | None:
    return RawRecord(port_entry).present(
        "aggregation_group",
        "aggregation_id",
        "aggregate_id",
        "agg_id",
        "lag_id",
        "lag_group",
        "link_aggregation_group",
        "link_aggregation_id",
        "aggregate",
        "aggregated_by",
        skip_values=(None, "", False),
    )


def _coerce_vlan_string(value: str) -> tuple[int, ...]:
    """Parse a comma-separated VLAN string to tuple of ints."""
    normalized = value.strip().lower()
    if normalized in ("auto", "block_all", "all", "none", ""):
        return ()
    parts = [p.strip() for p in value.split(",") if p.strip()]
    parsed = [_as_int(p) for p in parts]
    return tuple(sorted(v for v in parsed if v is not None))


def _coerce_vlan_sequence(
    items: list | tuple, network_vlan_map: dict[str, int] | None
) -> tuple[int, ...]:
    """Convert a sequence of VLAN IDs or network names to tuple of ints."""
    result: list[int] = []
    for item in items:
        parsed_int = _as_int(item)
        if parsed_int is not None:
            result.append(parsed_int)
        elif network_vlan_map and isinstance(item, str):
            vlan_id = network_vlan_map.get(item)
            if vlan_id is not None:
                result.append(vlan_id)
    return tuple(sorted(set(result)))


def _coerce_vlan_list(
    value: object, network_vlan_map: dict[str, int] | None = None
) -> tuple[int, ...]:
    """Convert a VLAN list from various formats to a tuple of ints."""
    if value is None:
        return ()
    if isinstance(value, str):
        return _coerce_vlan_string(value)
    if isinstance(value, int):
        return (value,)
    if isinstance(value, list | tuple):
        return _coerce_vlan_sequence(value, network_vlan_map)
    return ()


def _resolve_vlan_id(value: object, network_vlan_map: dict[str, int] | None = None) -> int | None:
    """Resolve a VLAN ID, which may be a network ID string."""
    parsed = _as_int(value)
    if parsed is not None:
        return parsed
    # Try to resolve network ID to VLAN number
    if network_vlan_map and isinstance(value, str):
        return network_vlan_map.get(value)
    return None


def _extract_wan_networkconf_id(port_entry: object) -> str | None:
    """Extract WAN network configuration ID from a port entry."""
    return RawRecord(port_entry).text("wan_networkconf_id")


def _port_info_from_entry(
    port_entry: object, network_vlan_map: dict[str, int] | None = None
) -> PortInfo:
    record = RawRecord(port_entry)
    return PortInfo(
        port_idx=record.integer("port_idx", "portIdx"),
        name=record.text("name"),
        ifname=record.text("ifname"),
        speed=record.integer("speed"),
        aggregation_group=_as_group_id(_aggregation_group(port_entry)),
        port_poe=as_bool(record.get("port_poe")),
        poe_enable=as_bool(record.get("poe_enable")),
        poe_good=as_bool(record.get("poe_good")),
        poe_power=_as_float(record.get("poe_power")),
        up=record.optional_bool("up"),
        native_vlan=_resolve_vlan_id(record.get("native_vlan"), network_vlan_map),
        tagged_vlans=_coerce_vlan_list(record.get("tagged_vlans"), network_vlan_map),
        wan_networkconf_id=_extract_wan_networkconf_id(port_entry),
    )


def _coerce_port_table(
    device: DeviceSource, network_vlan_map: dict[str, int] | None = None
) -> list[PortInfo]:
    port_table = as_list(get_field(device, "port_table"))
    return [_port_info_from_entry(port_entry, network_vlan_map) for port_entry in port_table]


def _poe_ports_from_device(
    device: DeviceSource, network_vlan_map: dict[str, int] | None = None
) -> dict[int, bool]:
    port_table = _coerce_port_table(device, network_vlan_map)
    poe_ports: dict[int, bool] = {}
    for port_entry in port_table:
        if port_entry.port_idx is None:
            continue
        active = (
            port_entry.poe_enable
            or port_entry.port_poe
            or port_entry.poe_good
            or _as_float(port_entry.poe_power) > 0.0
        )
        poe_ports[int(port_entry.port_idx)] = active
    return poe_ports


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
    port = _as_int(port_raw)
    if mac_value is None and name_value is None and port is None:
        return None
    return UplinkInfo(mac=mac_value, name=name_value, port=port)


def _uplink_info(device: DeviceSource) -> tuple[UplinkInfo | None, UplinkInfo | None]:
    uplink = _parse_uplink(get_field(device, "uplink"))
    last_uplink = _parse_uplink(get_field(device, "last_uplink"))

    if uplink is None:
        mac = get_field(device, "uplink_mac") or get_field(device, "uplink_device_mac")
        name = get_field(device, "uplink_device_name")
        port = _as_int(get_field(device, "uplink_remote_port"))
        uplink = _parse_uplink(
            {"uplink_mac": mac, "uplink_device_name": name, "uplink_remote_port": port}
        )

    if last_uplink is None:
        mac = get_field(device, "last_uplink_mac")
        last_uplink = _parse_uplink({"uplink_mac": mac})

    return uplink, last_uplink


def _get_model_display_name(device: DeviceSource) -> str | None:
    """Extract the human-readable model name from device data.

    UniFi stores the friendly model name (e.g., 'USW Flex 2.5G 8 PoE') in various
    fields depending on controller version. This function checks multiple candidates
    and returns the first non-empty value found.
    """
    candidates = (
        "model_in_lts",
        "model_in_eol",
        "shortname",
        "model_name",
    )
    return RawRecord(device).text(*candidates)


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


def _coerce_network_table(device: DeviceSource) -> list[dict[str, object]]:
    """Extract and validate network_table entries from device data."""
    raw = as_list(get_field(device, "network_table"))
    return [e for e in raw if isinstance(e, dict)]


def coerce_device(device: DeviceSource, network_vlan_map: dict[str, int] | None = None) -> Device:
    record = RawRecord(device)
    name = record.get("name")
    mac = record.get("mac")
    if not name or not mac:
        raise ValueError("Device missing name or mac")

    model_name, model, ip, dev_type, version = _device_display_fields(device)
    in_gateway_mode = _gateway_mode(device)

    uplink, last_uplink = _uplink_info(device)
    lldp_entries = _resolve_lldp_info(device, name, uplink, last_uplink)
    coerced_lldp = [coerce_lldp(entry) for entry in lldp_entries]
    port_table = _coerce_port_table(device, network_vlan_map)
    poe_ports = _poe_ports_from_device(device, network_vlan_map)
    network_table = _coerce_network_table(device)

    return Device(
        name=str(name),
        model_name=str(model_name or ""),
        model=str(model or ""),
        mac=str(mac),
        ip=str(ip or ""),
        type=str(dev_type or ""),
        lldp_info=coerced_lldp,
        port_table=port_table,
        poe_ports=poe_ports,
        uplink=uplink,
        last_uplink=last_uplink,
        version=str(version or ""),
        in_gateway_mode=in_gateway_mode,
        network_table=network_table,
    )


def normalize_devices(
    devices: Iterable[DeviceSource], network_vlan_map: dict[str, int] | None = None
) -> list[Device]:
    """Coerce raw device dicts/objects into typed :class:`Device` instances."""
    return [coerce_device(device, network_vlan_map) for device in devices]
