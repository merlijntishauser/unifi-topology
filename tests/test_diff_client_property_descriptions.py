"""Tests for client property-change topology diff descriptions."""

from __future__ import annotations

from unifi_topology.model.diff import compare_topologies


class TestClientPropertyDescriptions:
    def test_client_changed_ip(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "ip": "192.168.1.100",
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "ip": "192.168.1.200",
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "IP changed" in diff.events[0].description

    def test_client_changed_generic_property(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "channel": 36,
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "channel": 149,
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "channel changed" in diff.events[0].description

    def test_client_changed_multiple_properties(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "ip": "192.168.1.100",
            "channel": 36,
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "ip": "192.168.1.200",
            "channel": 149,
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "changed" in diff.events[0].description
        assert "properties" in diff.events[0].description

    def test_client_with_no_name_uses_mac(self):
        old_client: dict[str, object] = {
            "mac": "cc:dd:ee:ff:00:11",
            "ip": "192.168.1.100",
        }
        new_client: dict[str, object] = {
            "mac": "cc:dd:ee:ff:00:11",
            "ip": "192.168.1.200",
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "cc:dd:ee:ff:00:11" in diff.events[0].description
