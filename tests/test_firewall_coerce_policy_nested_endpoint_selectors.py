"""Tests for nested firewall policy endpoint selector normalization."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_policies

pytestmark = pytest.mark.unit


class TestNormalizePolicyNestedEndpointSelectors:
    def test_mac_addresses(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source": {
                        "zone_id": "z1",
                        "mac_addresses": ["AA:BB:CC:DD:EE:FF"],
                    },
                    "destination": {
                        "zone_id": "z2",
                        "mac_addresses": ["11:22:33:44:55:66"],
                    },
                },
            ]
        )
        assert policies[0].source_mac_addresses == ("AA:BB:CC:DD:EE:FF",)
        assert policies[0].destination_mac_addresses == ("11:22:33:44:55:66",)

    def test_network_ids(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source": {"zone_id": "z1", "network_id": "net1"},
                    "destination": {"zone_id": "z2", "network_id": "net2"},
                },
            ]
        )
        assert policies[0].source_network_id == "net1"
        assert policies[0].destination_network_id == "net2"

    def test_group_ids(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "x",
                    "enabled": True,
                    "action": "ALLOW",
                    "source": {
                        "zone_id": "z1",
                        "port_group_id": "pg1",
                        "address_group_id": "ag1",
                    },
                    "destination": {
                        "zone_id": "z2",
                        "port_group_id": "pg2",
                        "address_group_id": "ag2",
                    },
                },
            ]
        )
        assert policies[0].source_port_group_id == "pg1"
        assert policies[0].destination_port_group_id == "pg2"
        assert policies[0].source_address_group_id == "ag1"
        assert policies[0].destination_address_group_id == "ag2"
