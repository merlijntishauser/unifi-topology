"""Fields-introspection guards: no serialized dataclass field is dropped on load.

These characterization tests fail if a field is added to one of these
dataclasses but not wired into both its to_dict and from_dict.
"""

from __future__ import annotations

import dataclasses

from unifi_topology.model.connection import ConnectionInfo
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.snapshot import (
    connection_info_from_dict,
    connection_info_to_dict,
    lldp_entry_from_dict,
    lldp_entry_to_dict,
    port_info_from_dict,
    port_info_to_dict,
    uplink_info_from_dict,
    uplink_info_to_dict,
    wan_interface_from_dict,
    wan_interface_to_dict,
)
from unifi_topology.model.topology import PortInfo, UplinkInfo, WanInterface


def _assert_round_trip(original, to_dict, from_dict):
    restored = from_dict(to_dict(original))
    for field in dataclasses.fields(original):
        assert getattr(restored, field.name) == getattr(original, field.name), field.name


def test_port_info_round_trip_all_fields():
    port = PortInfo(
        port_idx=5,
        name="Port 5",
        ifname="eth4",
        speed=1000,
        aggregation_group="lag1",
        port_poe=True,
        poe_enable=True,
        poe_good=True,
        poe_power=12.5,
        up=True,
        native_vlan=10,
        tagged_vlans=(20, 30),
        wan_networkconf_id="WAN",
    )
    _assert_round_trip(port, port_info_to_dict, port_info_from_dict)


def test_uplink_info_round_trip_all_fields():
    uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name="Switch", port=5)
    _assert_round_trip(uplink, uplink_info_to_dict, uplink_info_from_dict)


def test_lldp_entry_round_trip_all_fields():
    entry = LLDPEntry(
        chassis_id="aa:bb:cc:dd:ee:ff",
        port_id="1",
        port_desc="desc",
        local_port_name="eth0",
        local_port_idx=1,
    )
    _assert_round_trip(entry, lldp_entry_to_dict, lldp_entry_from_dict)


def test_wan_interface_round_trip_all_fields():
    wan = WanInterface(
        port_idx=1,
        link_speed=1000,
        ip_address="1.2.3.4",
        enabled=True,
        label="Primary",
        isp_speed="1G",
        public_ip="5.6.7.8",
    )
    _assert_round_trip(wan, wan_interface_to_dict, wan_interface_from_dict)


def test_connection_info_round_trip_all_fields():
    conn = ConnectionInfo(
        signal_dbm=-50,
        noise_dbm=-90,
        tx_rate_mbps=866,
        rx_rate_mbps=866,
        satisfaction=95,
        quality="good",
    )
    _assert_round_trip(conn, connection_info_to_dict, connection_info_from_dict)
