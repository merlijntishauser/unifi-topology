"""Tests for snapshot serialization of LLDP and WAN structs."""

from __future__ import annotations

from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.snapshot import (
    lldp_entry_from_dict,
    lldp_entry_to_dict,
    wan_info_from_dict,
    wan_info_to_dict,
    wan_interface_from_dict,
    wan_interface_to_dict,
)
from unifi_topology.model.topology import WanInfo, WanInterface


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
