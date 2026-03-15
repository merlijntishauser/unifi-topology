"""Tests for firewall zone normalization."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_zones

pytestmark = pytest.mark.unit


class TestNormalizeZones:
    def test_basic(self):
        raw = [{"_id": "z1", "name": "IoT", "networkIds": ["n1", "n2"]}]
        zones = normalize_firewall_zones(raw)
        assert len(zones) == 1
        assert zones[0].id == "z1"
        assert zones[0].name == "IoT"
        assert zones[0].network_ids == ("n1", "n2")

    def test_alternative_field_names(self):
        raw = [{"id": "z1", "zone_name": "WAN", "network_ids": ["n1"]}]
        zones = normalize_firewall_zones(raw)
        assert zones[0].id == "z1"
        assert zones[0].name == "WAN"
        assert zones[0].network_ids == ("n1",)

    def test_skips_entries_without_id(self):
        raw = [{"name": "Bad"}, {"_id": "z1", "name": "Good"}]
        zones = normalize_firewall_zones(raw)
        assert len(zones) == 1
        assert zones[0].name == "Good"

    def test_empty_input(self):
        assert normalize_firewall_zones([]) == []

    def test_no_networks(self):
        zones = normalize_firewall_zones([{"_id": "z1", "name": "WAN"}])
        assert zones[0].network_ids == ()
