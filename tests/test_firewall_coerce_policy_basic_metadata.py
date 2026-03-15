"""Tests for firewall policy metadata and defaults."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_policies

pytestmark = pytest.mark.unit


class TestNormalizePolicyBasicMetadata:
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

    def test_defaults_for_new_fields(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source_zone_id": "z1",
                    "destination_zone_id": "z2",
                },
            ]
        )
        policy = policies[0]
        assert policy.source_ip_ranges == ()
        assert policy.source_mac_addresses == ()
        assert policy.source_port_ranges == ()
        assert policy.source_network_id == ""
        assert policy.destination_mac_addresses == ()
        assert policy.destination_network_id == ""
        assert policy.source_port_group_id == ""
        assert policy.destination_port_group_id == ""
        assert policy.source_address_group_id == ""
        assert policy.destination_address_group_id == ""
        assert policy.connection_state_type == ""
        assert policy.connection_logging is False
        assert policy.schedule == ""
        assert policy.match_ip_sec == ""
