"""Tests for VLAN info builders."""

from __future__ import annotations

from unifi_topology.model.vlans import build_vlan_info


class TestBuildVlanInfo:
    def test_empty_inputs(self):
        result = build_vlan_info([], [])
        assert result == []

    def test_networks_only(self):
        networks = [
            {"name": "LAN", "vlan_enabled": False},
            {"name": "Guest", "vlan": 20},
        ]
        result = build_vlan_info([], networks)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name"] == "LAN"
        assert result[0]["client_count"] == 0
        assert result[1]["id"] == 20
        assert result[1]["name"] == "Guest"

    def test_clients_only(self):
        clients = [
            {"vlan": 10},
            {"vlan": 10},
            {"vlan": 20},
        ]
        result = build_vlan_info(clients, [])
        assert len(result) == 2
        vlan_map = {r["id"]: r for r in result}
        assert vlan_map[10]["client_count"] == 2
        assert vlan_map[20]["client_count"] == 1
        assert vlan_map[10]["name"] is None

    def test_merges_clients_and_networks(self):
        networks = [{"name": "IoT", "vlan": 30}]
        clients = [{"vlan": 30}, {"vlan": 30}, {"vlan": 40}]
        result = build_vlan_info(clients, networks)
        vlan_map = {r["id"]: r for r in result}
        assert vlan_map[30]["name"] == "IoT"
        assert vlan_map[30]["client_count"] == 2
        assert vlan_map[40]["name"] is None
        assert vlan_map[40]["client_count"] == 1

    def test_clients_with_no_vlan_ignored(self):
        clients = [{"name": "Client A"}, {"vlan": 10}]
        result = build_vlan_info(clients, [])
        assert len(result) == 1
        assert result[0]["id"] == 10

    def test_results_sorted_by_vlan_id(self):
        networks = [
            {"name": "C", "vlan": 30},
            {"name": "A", "vlan": 10},
            {"name": "B", "vlan": 20},
        ]
        result = build_vlan_info([], networks)
        ids = [r["id"] for r in result]
        assert ids == [10, 20, 30]
