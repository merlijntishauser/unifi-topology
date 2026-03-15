"""Tests for firewall policy metadata fields."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_policies

pytestmark = pytest.mark.unit


class TestNormalizePolicyMetadataFields:
    def test_connection_state_type(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source_zone_id": "z1",
                    "destination_zone_id": "z2",
                    "connection_state_type": "ESTABLISHED",
                },
            ]
        )
        assert policies[0].connection_state_type == "ESTABLISHED"

    def test_connection_logging(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source_zone_id": "z1",
                    "destination_zone_id": "z2",
                    "connection_logging": True,
                },
            ]
        )
        assert policies[0].connection_logging is True

    def test_schedule(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source_zone_id": "z1",
                    "destination_zone_id": "z2",
                    "schedule": "weekdays-only",
                },
            ]
        )
        assert policies[0].schedule == "weekdays-only"

    def test_match_ip_sec(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source_zone_id": "z1",
                    "destination_zone_id": "z2",
                    "match_ip_sec": "MATCH_IPSEC",
                },
            ]
        )
        assert policies[0].match_ip_sec == "MATCH_IPSEC"
