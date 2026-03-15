"""Tests for client connection-related topology diff descriptions."""

from __future__ import annotations

from unifi_topology.model.diff import compare_topologies


class TestClientConnectionDescriptions:
    def test_client_wifi_description(self):
        wifi_client = {
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "phone",
            "is_wired": False,
        }
        diff = compare_topologies([], [], old_clients=[], new_clients=[wifi_client])
        assert "WiFi" in diff.events[0].description

    def test_client_wired_description(self):
        wired_client = {
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "desktop",
            "is_wired": True,
        }
        diff = compare_topologies([], [], old_clients=[], new_clients=[wired_client])
        assert "wired" in diff.events[0].description

    def test_client_changed_uplink_mac(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "sw_mac": "11:11:11:11:11:11",
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "sw_mac": "22:22:22:22:22:22",
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "moved to different device" in diff.events[0].description

    def test_client_changed_uplink_port(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "sw_port": 5,
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "sw_port": 10,
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "moved to port" in diff.events[0].description
