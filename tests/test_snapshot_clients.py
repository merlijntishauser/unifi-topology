"""Tests for snapshot serialization of clients."""

from __future__ import annotations

from unifi_topology.model.snapshot import client_from_dict, client_to_dict


class TestClientSerialization:
    def test_filters_relevant_keys(self):
        client = {
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "laptop",
            "ip": "192.168.1.100",
            "vlan": 10,
            "is_wired": True,
            "sw_mac": "11:22:33:44:55:66",
            "sw_port": 5,
            "irrelevant_field": "should_be_excluded",
            "another_field": 123,
        }
        data = client_to_dict(client)
        assert "mac" in data
        assert "name" in data
        assert "irrelevant_field" not in data
        assert "another_field" not in data

    def test_from_dict_preserves_all(self):
        client = client_from_dict({"mac": "aa:bb:cc:dd:ee:ff", "name": "test", "custom": "value"})
        assert client["mac"] == "aa:bb:cc:dd:ee:ff"
        assert client["custom"] == "value"
