"""Tests for VLAN network normalization."""

from __future__ import annotations

from unifi_topology.model.vlans import normalize_networks


class TestNormalizeNetworks:
    def test_empty_input(self):
        assert normalize_networks([]) == []

    def test_extracts_network_fields(self):
        networks = [{"_id": "net1", "name": "LAN", "vlan": 10, "vlan_enabled": True}]
        result = normalize_networks(networks)
        assert len(result) == 1
        assert result[0]["network_id"] == "net1"
        assert result[0]["name"] == "LAN"
        assert result[0]["vlan_id"] == 10
        assert result[0]["vlan_enabled"] is True

    def test_alternative_field_names(self):
        networks = [{"id": "net2", "network_name": "Guest", "vlanId": 20, "vlanEnabled": True}]
        result = normalize_networks(networks)
        assert result[0]["network_id"] == "net2"
        assert result[0]["name"] == "Guest"
        assert result[0]["vlan_id"] == 20

    def test_vlan_disabled_defaults_to_vlan_1(self):
        networks = [{"name": "Default", "vlan_enabled": False}]
        result = normalize_networks(networks)
        assert result[0]["vlan_id"] == 1

    def test_skips_none_entries(self):
        networks = [{"name": "Valid"}, None, {"name": "Also Valid"}]
        result = normalize_networks(networks)
        assert len(result) == 2

    def test_string_vlan_id(self):
        networks = [{"name": "Test", "vlan": "30", "vlan_enabled": True}]
        result = normalize_networks(networks)
        assert result[0]["vlan_id"] == 30

    def test_invalid_vlan_id_zero(self):
        networks = [{"name": "Test", "vlan": 0, "vlan_enabled": True}]
        result = normalize_networks(networks)
        assert result[0]["vlan_id"] is None

    def test_invalid_vlan_id_negative(self):
        networks = [{"name": "Test", "vlan": -1, "vlan_enabled": True}]
        result = normalize_networks(networks)
        assert result[0]["vlan_id"] is None

    def test_purpose_field(self):
        networks = [{"name": "Corp", "purpose": "corporate", "vlan": 100}]
        result = normalize_networks(networks)
        assert result[0]["purpose"] == "corporate"

    def test_enabled_field_present(self):
        networks = [{"name": "WAN", "purpose": "wan", "enabled": True}]
        result = normalize_networks(networks)
        assert result[0]["enabled"] is True

    def test_enabled_field_false(self):
        networks = [{"name": "WAN2", "purpose": "wan2", "enabled": False}]
        result = normalize_networks(networks)
        assert result[0]["enabled"] is False

    def test_enabled_field_absent(self):
        networks = [{"name": "LAN", "purpose": "corporate"}]
        result = normalize_networks(networks)
        assert result[0]["enabled"] is None
