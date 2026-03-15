"""Type coercion and device normalization utilities."""

from __future__ import annotations

from . import _topology_device_coerce, _topology_port_coerce

__all__ = [
    "_aggregation_group",
    "_as_float",
    "_as_group_id",
    "_as_int",
    "_coerce_network_table",
    "_coerce_port_table",
    "_coerce_uplink_string",
    "_coerce_vlan_list",
    "_coerce_vlan_sequence",
    "_coerce_vlan_string",
    "_device_display_fields",
    "_extract_uplink_fields",
    "_extract_wan_networkconf_id",
    "_gateway_mode",
    "_get_lldp_info",
    "_get_model_display_name",
    "_parse_uplink",
    "_poe_ports_from_device",
    "_port_info_from_entry",
    "_resolve_lldp_info",
    "_resolve_vlan_id",
    "_uplink_info",
    "coerce_device",
    "normalize_devices",
]

_aggregation_group = _topology_port_coerce._aggregation_group
_as_float = _topology_port_coerce._as_float
_as_group_id = _topology_port_coerce._as_group_id
_as_int = _topology_port_coerce._as_int
_coerce_network_table = _topology_port_coerce._coerce_network_table
_coerce_port_table = _topology_port_coerce._coerce_port_table
_coerce_uplink_string = _topology_device_coerce._coerce_uplink_string
_coerce_vlan_list = _topology_port_coerce._coerce_vlan_list
_coerce_vlan_sequence = _topology_port_coerce._coerce_vlan_sequence
_coerce_vlan_string = _topology_port_coerce._coerce_vlan_string
_device_display_fields = _topology_device_coerce._device_display_fields
_extract_uplink_fields = _topology_device_coerce._extract_uplink_fields
_extract_wan_networkconf_id = _topology_port_coerce._extract_wan_networkconf_id
_gateway_mode = _topology_device_coerce._gateway_mode
_get_lldp_info = _topology_device_coerce._get_lldp_info
_get_model_display_name = _topology_device_coerce._get_model_display_name
_parse_uplink = _topology_device_coerce._parse_uplink
_poe_ports_from_device = _topology_port_coerce._poe_ports_from_device
_port_info_from_entry = _topology_port_coerce._port_info_from_entry
_resolve_lldp_info = _topology_device_coerce._resolve_lldp_info
_resolve_vlan_id = _topology_port_coerce._resolve_vlan_id
_uplink_info = _topology_device_coerce._uplink_info
coerce_device = _topology_device_coerce.coerce_device
normalize_devices = _topology_device_coerce.normalize_devices
