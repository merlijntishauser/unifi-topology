"""Tests for basic firewall policy field normalization."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_policies

pytestmark = pytest.mark.unit


class TestNormalizePolicyBasicFields:
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
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "allow",
                    "source_zone_id": "z1",
                    "destination_zone_id": "z2",
                },
            ]
        )
        assert policies[0].action == "ALLOW"

    def test_predefined(self):
        policies = normalize_firewall_policies(
            [
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
        )
        assert policies[0].predefined is True

    def test_port_ranges(self):
        policies = normalize_firewall_policies(
            [
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
        )
        assert policies[0].port_ranges == ("80", "443")

    def test_alternative_field_names(self):
        policies = normalize_firewall_policies(
            [
                {
                    "id": "p1",
                    "policy_name": "x",
                    "enabled": True,
                    "policy_action": "block",
                    "sourceZoneId": "z1",
                    "destinationZoneId": "z2",
                },
            ]
        )
        assert policies[0].source_zone_id == "z1"
        assert policies[0].destination_zone_id == "z2"
        assert policies[0].action == "BLOCK"
