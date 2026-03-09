"""Tests for firewall data normalization."""

import pytest

from unifi_topology.model.firewall_coerce import (
    normalize_firewall_groups,
    normalize_firewall_policies,
    normalize_firewall_zones,
)

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
        raw = [{"_id": "z1", "name": "WAN"}]
        zones = normalize_firewall_zones(raw)
        assert zones[0].network_ids == ()


class TestNormalizePolicies:
    def test_basic(self):
        raw = [
            {
                "_id": "p1",
                "name": "Block IoT to LAN",
                "enabled": True,
                "action": "BLOCK",
                "source_zone_id": "z_iot",
                "destination_zone_id": "z_lan",
                "protocol": "all",
                "index": 100,
            },
        ]
        policies = normalize_firewall_policies(raw)
        assert len(policies) == 1
        assert policies[0].action == "BLOCK"
        assert policies[0].source_zone_id == "z_iot"
        assert policies[0].index == 100

    def test_action_uppercased(self):
        raw = [
            {
                "_id": "p1",
                "name": "x",
                "enabled": True,
                "action": "allow",
                "source_zone_id": "z1",
                "destination_zone_id": "z2",
            },
        ]
        policies = normalize_firewall_policies(raw)
        assert policies[0].action == "ALLOW"

    def test_predefined(self):
        raw = [
            {
                "_id": "p1",
                "name": "x",
                "enabled": True,
                "action": "ALLOW",
                "source_zone_id": "z1",
                "destination_zone_id": "z2",
                "predefined": True,
            },
        ]
        policies = normalize_firewall_policies(raw)
        assert policies[0].predefined is True

    def test_port_ranges(self):
        raw = [
            {
                "_id": "p1",
                "name": "x",
                "enabled": True,
                "action": "ALLOW",
                "source_zone_id": "z1",
                "destination_zone_id": "z2",
                "port_ranges": ["80", "443"],
            },
        ]
        policies = normalize_firewall_policies(raw)
        assert policies[0].port_ranges == ("80", "443")

    def test_alternative_field_names(self):
        raw = [
            {
                "id": "p1",
                "policy_name": "x",
                "enabled": True,
                "policy_action": "block",
                "sourceZoneId": "z1",
                "destinationZoneId": "z2",
            },
        ]
        policies = normalize_firewall_policies(raw)
        assert policies[0].source_zone_id == "z1"
        assert policies[0].destination_zone_id == "z2"
        assert policies[0].action == "BLOCK"

    def test_nested_zone_ids(self):
        """Zone IDs nested in source/destination dicts (v2 API format)."""
        raw = [
            {
                "_id": "p1",
                "name": "Allow mDNS",
                "enabled": True,
                "action": "ALLOW",
                "protocol": "udp",
                "source": {"zone_id": "z_internal", "port": "5353", "port_matching_type": "SPECIFIC"},
                "destination": {
                    "zone_id": "z_gateway",
                    "port": "5353",
                    "port_matching_type": "SPECIFIC",
                    "ips": ["224.0.0.251"],
                },
                "index": 30000,
                "predefined": True,
            },
        ]
        policies = normalize_firewall_policies(raw)
        assert policies[0].source_zone_id == "z_internal"
        assert policies[0].destination_zone_id == "z_gateway"
        assert policies[0].port_ranges == ("5353",)
        assert policies[0].ip_ranges == ("224.0.0.251",)

    def test_nested_zone_ids_any_port(self):
        """Nested format with ANY port matching should yield empty port_ranges."""
        raw = [
            {
                "_id": "p1",
                "name": "Allow All",
                "enabled": True,
                "action": "ALLOW",
                "source": {"zone_id": "z1", "port_matching_type": "ANY"},
                "destination": {"zone_id": "z2", "port_matching_type": "ANY"},
            },
        ]
        policies = normalize_firewall_policies(raw)
        assert policies[0].port_ranges == ()
        assert policies[0].ip_ranges == ()

    def test_flat_zone_ids_take_priority_over_nested(self):
        """Flat source_zone_id should take priority over nested source.zone_id."""
        raw = [
            {
                "_id": "p1",
                "name": "x",
                "enabled": True,
                "action": "ALLOW",
                "source_zone_id": "flat_src",
                "destination_zone_id": "flat_dst",
                "source": {"zone_id": "nested_src"},
                "destination": {"zone_id": "nested_dst"},
            },
        ]
        policies = normalize_firewall_policies(raw)
        assert policies[0].source_zone_id == "flat_src"
        assert policies[0].destination_zone_id == "flat_dst"


class TestNormalizeGroups:
    def test_basic(self):
        raw = [
            {
                "_id": "g1",
                "name": "DNS",
                "group_type": "address-group",
                "group_members": ["1.1.1.1", "8.8.8.8"],
            },
        ]
        groups = normalize_firewall_groups(raw)
        assert len(groups) == 1
        assert groups[0].members == ("1.1.1.1", "8.8.8.8")

    def test_empty_members(self):
        raw = [{"_id": "g1", "name": "Empty", "group_type": "port-group"}]
        groups = normalize_firewall_groups(raw)
        assert groups[0].members == ()
