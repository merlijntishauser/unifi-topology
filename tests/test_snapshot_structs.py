"""Tests for snapshot serialization of core model structs."""

from __future__ import annotations

from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.snapshot import (
    _serialize_value,
    lldp_entry_from_dict,
    lldp_entry_to_dict,
    port_info_from_dict,
    port_info_to_dict,
    uplink_info_from_dict,
    uplink_info_to_dict,
    wan_info_from_dict,
    wan_info_to_dict,
    wan_interface_from_dict,
    wan_interface_to_dict,
)
from unifi_topology.model.topology import PortInfo, UplinkInfo, WanInfo, WanInterface


class TestPortInfoSerialization:
    def test_round_trip(self):
        port = PortInfo(
            port_idx=1,
            name="Port 1",
            ifname="eth0",
            speed=1000,
            aggregation_group="lag1",
            port_poe=True,
            poe_enable=True,
            poe_good=True,
            poe_power=15.5,
            native_vlan=10,
            tagged_vlans=(20, 30),
            wan_networkconf_id="WAN",
        )
        data = port_info_to_dict(port)
        restored = port_info_from_dict(data)
        assert restored.port_idx == 1
        assert restored.name == "Port 1"
        assert restored.speed == 1000
        assert restored.poe_power == 15.5
        assert restored.tagged_vlans == (20, 30)

    def test_defaults_for_missing_fields(self):
        port = port_info_from_dict({"port_idx": 5})
        assert port.port_idx == 5
        assert port.name is None
        assert port.port_poe is False
        assert port.tagged_vlans == ()


class TestUplinkInfoSerialization:
    def test_round_trip(self):
        uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name="Switch", port=24)
        data = uplink_info_to_dict(uplink)
        restored = uplink_info_from_dict(data)
        assert restored.mac == "aa:bb:cc:dd:ee:ff"
        assert restored.name == "Switch"
        assert restored.port == 24

    def test_handles_none_values(self):
        uplink = UplinkInfo(mac=None, name=None, port=None)
        restored = uplink_info_from_dict(uplink_info_to_dict(uplink))
        assert restored.mac is None


class TestLLDPEntrySerialization:
    def test_round_trip(self):
        entry = LLDPEntry(
            chassis_id="aa:bb:cc:dd:ee:ff",
            port_id="eth0",
            port_desc="Uplink to Core",
            local_port_name="Port 24",
            local_port_idx=24,
        )
        data = lldp_entry_to_dict(entry)
        restored = lldp_entry_from_dict(data)
        assert restored.chassis_id == "aa:bb:cc:dd:ee:ff"
        assert restored.port_id == "eth0"
        assert restored.port_desc == "Uplink to Core"
        assert restored.local_port_idx == 24

    def test_defaults_for_missing_fields(self):
        entry = lldp_entry_from_dict({"chassis_id": "aa:bb:cc:dd:ee:ff"})
        assert entry.chassis_id == "aa:bb:cc:dd:ee:ff"
        assert entry.port_id == ""
        assert entry.port_desc is None


class TestWanInterfaceSerialization:
    def test_round_trip(self):
        wan = WanInterface(
            port_idx=1,
            link_speed=10000,
            ip_address="203.0.113.1",
            enabled=True,
            label="Fiber",
            isp_speed="1000/1000",
        )
        restored = wan_interface_from_dict(wan_interface_to_dict(wan))
        assert restored.port_idx == 1
        assert restored.link_speed == 10000
        assert restored.ip_address == "203.0.113.1"
        assert restored.enabled is True
        assert restored.label == "Fiber"
        assert restored.isp_speed == "1000/1000"


class TestWanInfoSerialization:
    def test_round_trip_single_wan(self):
        wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        restored = wan_info_from_dict(wan_info_to_dict(WanInfo(wan1=wan1, wan2=None)))
        assert restored.wan1 is not None
        assert restored.wan1.port_idx == 1
        assert restored.wan2 is None

    def test_round_trip_dual_wan(self):
        wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        wan2 = WanInterface(port_idx=9, link_speed=100, ip_address=None, enabled=False)
        restored = wan_info_from_dict(wan_info_to_dict(WanInfo(wan1=wan1, wan2=wan2)))
        assert restored.wan1 is not None
        assert restored.wan2 is not None
        assert restored.wan2.port_idx == 9


class TestSerializeValue:
    def test_list_serialization(self):
        assert _serialize_value([1, "two", None]) == [1, "two", None]

    def test_dict_serialization(self):
        assert _serialize_value({"a": 1, "b": "two"}) == {"a": 1, "b": "two"}

    def test_nested_dataclass_serialization(self):
        uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name="Switch", port=24)
        assert _serialize_value(uplink) == {
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "Switch",
            "port": 24,
        }

    def test_fallback_to_str(self):
        result = _serialize_value(object.__class__)
        assert isinstance(result, str)

    def test_nested_list_of_dataclasses(self):
        entries = [
            LLDPEntry(chassis_id="aa:bb", port_id="eth0"),
            LLDPEntry(chassis_id="cc:dd", port_id="eth1"),
        ]
        result = _serialize_value(entries)
        assert len(result) == 2
        assert result[0]["chassis_id"] == "aa:bb"
        assert result[1]["port_id"] == "eth1"

    def test_dict_with_nested_values(self):
        result = _serialize_value({"uplink": UplinkInfo(mac="aa:bb", name="S", port=1)})
        assert result["uplink"]["mac"] == "aa:bb"


class TestWanInfoNullBranches:
    def test_wan_info_both_none(self):
        data = wan_info_to_dict(WanInfo(wan1=None, wan2=None))
        assert data["wan1"] is None
        assert data["wan2"] is None

    def test_wan_info_from_dict_with_wan2(self):
        restored = wan_info_from_dict(
            {
                "wan1": None,
                "wan2": {
                    "port_idx": 9,
                    "link_speed": 100,
                    "ip_address": "10.0.0.1",
                    "enabled": True,
                },
            }
        )
        assert restored.wan1 is None
        assert restored.wan2 is not None
        assert restored.wan2.port_idx == 9
        assert restored.wan2.ip_address == "10.0.0.1"
