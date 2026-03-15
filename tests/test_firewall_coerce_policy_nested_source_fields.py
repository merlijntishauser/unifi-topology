"""Tests for nested firewall policy source field normalization."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_policies

pytestmark = pytest.mark.unit


class TestNormalizePolicyNestedSourceFields:
    def test_source_ip_ranges_flat(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source_zone_id": "z1",
                    "destination_zone_id": "z2",
                    "source_ip_ranges": ["10.0.0.0/8"],
                },
            ]
        )
        assert policies[0].source_ip_ranges == ("10.0.0.0/8",)

    def test_source_ip_ranges_nested(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source": {"zone_id": "z1", "ips": ["192.168.1.0/24"]},
                    "destination": {"zone_id": "z2"},
                },
            ]
        )
        assert policies[0].source_ip_ranges == ("192.168.1.0/24",)

    def test_source_port_ranges_nested(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source": {
                        "zone_id": "z1",
                        "port": "8080",
                        "port_matching_type": "SPECIFIC",
                    },
                    "destination": {"zone_id": "z2"},
                },
            ]
        )
        assert policies[0].source_port_ranges == ("8080",)

    def test_source_port_ranges_any(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source": {"zone_id": "z1", "port_matching_type": "ANY"},
                    "destination": {"zone_id": "z2"},
                },
            ]
        )
        assert policies[0].source_port_ranges == ()
