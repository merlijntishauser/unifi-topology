"""Tests for VLAN naming and network ID maps."""

from __future__ import annotations

from unifi_topology.model.vlans import build_network_vlan_map, build_vlan_names


class TestBuildNetworkVlanMap:
    def test_empty_networks(self):
        assert build_network_vlan_map([]) == {}

    def test_maps_network_id_to_vlan(self):
        networks = [
            {"_id": "net1", "vlan": 10},
            {"_id": "net2", "vlan": 20},
        ]
        result = build_network_vlan_map(networks)
        assert result == {"net1": 10, "net2": 20}

    def test_skips_missing_network_id(self):
        networks = [
            {"vlan": 10},
            {"_id": "net2", "vlan": 20},
        ]
        result = build_network_vlan_map(networks)
        assert result == {"net2": 20}

    def test_defaults_to_vlan_1_when_missing(self):
        networks = [
            {"_id": "net1"},
            {"_id": "net2", "vlan": 20},
        ]
        result = build_network_vlan_map(networks)
        assert result == {"net1": 1, "net2": 20}


class TestBuildVlanNames:
    def test_empty_networks(self):
        assert build_vlan_names([]) == {}

    def test_maps_vlan_to_name(self):
        networks = [
            {"name": "LAN", "vlan_enabled": False},
            {"name": "Guest", "vlan": 20},
        ]
        result = build_vlan_names(networks)
        assert result == {1: "LAN", 20: "Guest"}

    def test_first_name_wins_for_duplicate_vlans(self):
        networks = [
            {"name": "First", "vlan": 10},
            {"name": "Second", "vlan": 10},
        ]
        result = build_vlan_names(networks)
        assert result[10] == "First"

    def test_skips_networks_without_name(self):
        networks = [
            {"vlan": 10},
            {"name": "Named", "vlan": 20},
        ]
        result = build_vlan_names(networks)
        assert 10 not in result
        assert result[20] == "Named"
