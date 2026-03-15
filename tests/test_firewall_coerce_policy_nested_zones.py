"""Tests for nested firewall policy zone normalization."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_policies

pytestmark = pytest.mark.unit


class TestNormalizePolicyNestedZones:
    def test_nested_zone_ids(self):
        raw = [
            {
                "_id": "p1",
                "name": "Allow mDNS",
                "enabled": True,
                "action": "ALLOW",
                "protocol": "udp",
                "source": {
                    "zone_id": "z_internal",
                    "port": "5353",
                    "port_matching_type": "SPECIFIC",
                },
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
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "Allow All",
                    "enabled": True,
                    "action": "ALLOW",
                    "source": {"zone_id": "z1", "port_matching_type": "ANY"},
                    "destination": {"zone_id": "z2", "port_matching_type": "ANY"},
                },
            ]
        )

        assert policies[0].port_ranges == ()
        assert policies[0].ip_ranges == ()

    def test_flat_zone_ids_take_priority_over_nested(self):
        policies = normalize_firewall_policies(
            [
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
        )

        assert policies[0].source_zone_id == "flat_src"
        assert policies[0].destination_zone_id == "flat_dst"
