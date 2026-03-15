"""Private cache serialization helpers for the UniFi adapter."""

from __future__ import annotations

from collections.abc import Sequence

from ..model.helpers import as_list, first_attr, get_field
from ..model.lldp import coerce_lldp
from ..model.snapshot import lldp_entry_to_dict


def _serialize_lldp_entries(value: object | None) -> list[dict[str, object]]:
    serialized: list[dict[str, object]] = []
    for entry in as_list(value):
        try:
            lldp = coerce_lldp(entry)
        except ValueError:
            continue
        serialized.append(lldp_entry_to_dict(lldp))
    return serialized


def _serialize_port_entry(entry: object) -> dict[str, object]:
    aggregation_group = first_attr(
        entry,
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
    )
    native_vlan = first_attr(
        entry,
        "native_networkconf_id",
        "port_vlan",
        "vlan",
        "native_vlan",
        "pvid",
    )
    tagged_vlans = first_attr(
        entry,
        "tagged_vlan_mgmt",
        "tagged_vlans",
        "vlan_trunk_mgmt",
        "allowed_vlans",
    )
    return {
        "port_idx": first_attr(entry, "port_idx", "portIdx"),
        "name": first_attr(entry, "name"),
        "ifname": first_attr(entry, "ifname"),
        "speed": first_attr(entry, "speed"),
        "up": first_attr(entry, "up"),
        "aggregation_group": aggregation_group,
        "port_poe": first_attr(entry, "port_poe"),
        "poe_enable": first_attr(entry, "poe_enable"),
        "poe_good": first_attr(entry, "poe_good"),
        "poe_power": first_attr(entry, "poe_power"),
        "native_vlan": native_vlan,
        "tagged_vlans": tagged_vlans,
        "wan_networkconf_id": first_attr(entry, "wan_networkconf_id"),
    }


def _serialize_port_table(value: object | None) -> list[dict[str, object]]:
    return [_serialize_port_entry(entry) for entry in as_list(value)]


def _serialize_uplink(value: object | None) -> dict[str, object] | None:
    if value is None:
        return None
    data = {
        "uplink_mac": first_attr(value, "uplink_mac", "uplink_device_mac"),
        "uplink_device_name": first_attr(value, "uplink_device_name", "uplink_name"),
        "uplink_remote_port": first_attr(value, "uplink_remote_port", "port_idx"),
    }
    if any(item is not None for item in data.values()):
        return data
    return None


def _device_lldp_value(device: object) -> object | None:
    lldp_info = get_field(device, "lldp_info")
    if lldp_info is None:
        lldp_info = get_field(device, "lldp")
    if lldp_info is None:
        lldp_info = get_field(device, "lldp_table")
    return lldp_info


def _device_uplink_fields(device: object) -> dict[str, object | None]:
    return {
        "uplink": _serialize_uplink(get_field(device, "uplink")),
        "last_uplink": _serialize_uplink(get_field(device, "last_uplink")),
        "uplink_mac": first_attr(device, "uplink_mac", "uplink_device_mac"),
        "uplink_device_name": get_field(device, "uplink_device_name"),
        "uplink_remote_port": get_field(device, "uplink_remote_port"),
        "last_uplink_mac": get_field(device, "last_uplink_mac"),
    }


def _serialize_network_table(value: object | None) -> list[dict[str, object]]:
    """Serialize network_table entries for cache (preserves VPN tunnel data)."""
    entries = as_list(value)
    return [dict(entry) for entry in entries if isinstance(entry, dict)]


def _serialize_device_for_cache(device: object) -> dict[str, object]:
    payload = {
        "name": get_field(device, "name"),
        "model_name": get_field(device, "model_name"),
        "model": get_field(device, "model"),
        "mac": get_field(device, "mac"),
        "ip": first_attr(device, "ip", "ip_address"),
        "type": first_attr(device, "type", "device_type"),
        "in_gateway_mode": get_field(device, "in_gateway_mode"),
        "displayable_version": first_attr(device, "displayable_version", "version"),
        "lldp_info": _serialize_lldp_entries(_device_lldp_value(device)),
        "port_table": _serialize_port_table(get_field(device, "port_table")),
        "network_table": _serialize_network_table(get_field(device, "network_table")),
    }
    payload.update(_device_uplink_fields(device))
    return payload


def _serialize_devices_for_cache(devices: Sequence[object]) -> list[dict[str, object]]:
    return [_serialize_device_for_cache(device) for device in devices]


def _serialize_network_for_cache(network: object) -> dict[str, object]:
    return {
        "_id": first_attr(network, "_id", "id", "network_id", "networkId"),
        "name": first_attr(network, "name", "network_name", "networkName"),
        "vlan": first_attr(network, "vlan", "vlan_id", "vlanId", "vlanid"),
        "vlan_enabled": first_attr(network, "vlan_enabled", "vlanEnabled"),
        "purpose": first_attr(network, "purpose"),
        "enabled": first_attr(network, "enabled", "wan_enabled"),
    }


def _serialize_networks_for_cache(networks: Sequence[object]) -> list[dict[str, object]]:
    return [_serialize_network_for_cache(network) for network in networks]
