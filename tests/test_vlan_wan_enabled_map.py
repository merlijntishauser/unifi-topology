"""Tests for WAN-enabled VLAN maps."""

from __future__ import annotations

from unifi_topology.model.vlans import build_wan_enabled_map


class TestBuildWanEnabledMap:
    def test_empty_networks(self):
        assert build_wan_enabled_map([]) == {}

    def test_wan_enabled_wan2_disabled(self):
        networks = [
            {"name": "WAN", "purpose": "wan", "enabled": True},
            {"name": "WAN2", "purpose": "wan2", "enabled": False},
        ]
        result = build_wan_enabled_map(networks)
        assert result == {"wan": True, "wan2": False}

    def test_ignores_non_wan_networks(self):
        networks = [
            {"name": "LAN", "purpose": "corporate", "enabled": True},
            {"name": "WAN", "purpose": "wan", "enabled": True},
        ]
        result = build_wan_enabled_map(networks)
        assert result == {"wan": True}

    def test_skips_networks_without_enabled(self):
        networks = [
            {"name": "WAN", "purpose": "wan"},
            {"name": "WAN2", "purpose": "wan2", "enabled": False},
        ]
        result = build_wan_enabled_map(networks)
        assert result == {"wan2": False}
