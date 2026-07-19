"""Tests for port topology coercion helpers."""

from __future__ import annotations

from unifi_topology.model._topology_port_coerce import (
    _extract_wan_networkconf_id,
    _port_info_from_entry,
)


class TestExtractWanNetworkconfId:
    def test_dict_with_value(self):
        assert _extract_wan_networkconf_id({"wan_networkconf_id": "WAN"}) == "WAN"

    def test_dict_with_empty_value(self):
        assert _extract_wan_networkconf_id({"wan_networkconf_id": "  "}) is None

    def test_dict_without_field(self):
        assert _extract_wan_networkconf_id({}) is None

    def test_non_dict_object_with_attribute(self):
        class MockPort:
            def __init__(self):
                self.wan_networkconf_id = "WAN2"

        assert _extract_wan_networkconf_id(MockPort()) == "WAN2"


class TestPortInfoFromEntry:
    def test_dict_port_entry(self):
        entry = {
            "port_idx": 1,
            "name": "Port 1",
            "ifname": "eth0",
            "speed": 1000,
            "port_poe": True,
            "poe_power": 15.5,
        }
        port = _port_info_from_entry(entry)
        assert port.port_idx == 1
        assert port.name == "Port 1"
        assert port.speed == 1000
        assert port.port_poe is True

    def test_non_dict_port_entry(self):
        class MockPort:
            def __init__(self):
                self.port_idx = 5
                self.portIdx = None
                self.name = "SFP"
                self.ifname = "sfp0"
                self.speed = 10000
                self.aggregation_group = None
                self.port_poe = False
                self.poe_enable = False
                self.poe_good = False
                self.poe_power = 0.0
                self.native_vlan = 10
                self.tagged_vlans = (20, 30)

        port = _port_info_from_entry(MockPort())
        assert port.port_idx == 5
        assert port.name == "SFP"
        assert port.speed == 10000

    def test_with_network_vlan_map(self):
        entry = {
            "port_idx": 1,
            "native_vlan": "network_lan",
            "tagged_vlans": ["network_guest", "network_iot"],
        }
        network_map = {"network_lan": 1, "network_guest": 20, "network_iot": 30}
        port = _port_info_from_entry(entry, network_map)
        assert port.native_vlan == 1
        assert port.tagged_vlans == (20, 30)
