"""Tests for uplink topology coercion helpers."""

from __future__ import annotations

from unifi_topology.model.topology_coerce import _parse_uplink


class TestParseUplink:
    def test_none_returns_none(self):
        assert _parse_uplink(None) is None

    def test_dict_with_fields(self):
        uplink = _parse_uplink(
            {
                "uplink_mac": "aa:bb:cc:dd:ee:ff",
                "uplink_device_name": "Core Switch",
                "uplink_remote_port": 24,
            }
        )
        assert uplink is not None
        assert uplink.mac == "aa:bb:cc:dd:ee:ff"
        assert uplink.name == "Core Switch"
        assert uplink.port == 24

    def test_all_none_returns_none(self):
        assert _parse_uplink({}) is None

    def test_non_dict_with_fields(self):
        class MockUplink:
            def __init__(self):
                self.uplink_mac = "11:22:33:44:55:66"
                self.uplink_device_mac = None
                self.uplink_device_name = "Switch"
                self.uplink_name = None
                self.uplink_remote_port = 10
                self.port_idx = None

        uplink = _parse_uplink(MockUplink())
        assert uplink is not None
        assert uplink.mac == "11:22:33:44:55:66"
