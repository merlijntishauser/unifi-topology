"""Private helpers for coercing device port and VLAN data."""

from __future__ import annotations

from ._raw import RawRecord
from .helpers import as_bool, as_list, get_field
from .topology import DeviceSource, PortInfo


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
    if value is None or isinstance(value, bool):
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


def _is_empty_vlan_string(value: str) -> bool:
    return value.strip().lower() in ("auto", "block_all", "all", "none", "")


def _coerce_vlan_string(value: str) -> tuple[int, ...]:
    """Parse a comma-separated VLAN string to tuple of ints."""
    if _is_empty_vlan_string(value):
        return ()
    parts = [part.strip() for part in value.split(",") if part.strip()]
    parsed = [_as_int(part) for part in parts]
    return tuple(sorted(vlan for vlan in parsed if vlan is not None))


def _resolved_sequence_vlan(
    item: object,
    network_vlan_map: dict[str, int] | None,
) -> int | None:
    parsed_int = _as_int(item)
    if parsed_int is not None:
        return parsed_int
    if network_vlan_map and isinstance(item, str):
        return network_vlan_map.get(item)
    return None


def _coerce_vlan_sequence(
    items: list | tuple, network_vlan_map: dict[str, int] | None
) -> tuple[int, ...]:
    """Convert a sequence of VLAN IDs or network names to tuple of ints."""
    resolved = [
        vlan_id
        for item in items
        if (vlan_id := _resolved_sequence_vlan(item, network_vlan_map)) is not None
    ]
    return tuple(sorted(set(resolved)))


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


def _port_has_active_poe(port_entry: PortInfo) -> bool:
    return (
        port_entry.poe_enable
        or port_entry.port_poe
        or port_entry.poe_good
        or _as_float(port_entry.poe_power) > 0.0
    )


def _poe_ports_from_device(
    device: DeviceSource, network_vlan_map: dict[str, int] | None = None
) -> dict[int, bool]:
    port_table = _coerce_port_table(device, network_vlan_map)
    poe_ports: dict[int, bool] = {}
    for port_entry in port_table:
        if port_entry.port_idx is None:
            continue
        poe_ports[int(port_entry.port_idx)] = _port_has_active_poe(port_entry)
    return poe_ports


def _coerce_network_table(device: DeviceSource) -> list[dict[str, object]]:
    """Extract and validate network_table entries from device data."""
    raw = as_list(get_field(device, "network_table"))
    return [entry for entry in raw if isinstance(entry, dict)]
