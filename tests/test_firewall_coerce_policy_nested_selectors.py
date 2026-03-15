"""Tests for nested firewall policy selector normalization."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_policies

pytestmark = pytest.mark.unit


class TestNormalizePolicyNestedSelectors:
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

    def test_full_v2_nested_entry(self):
        policies = normalize_firewall_policies(
            [
                {
                    "_id": "p1",
                    "name": "Restrict IoT",
                    "enabled": True,
                    "action": "ALLOW",
                    "protocol": "tcp",
                    "source": {
                        "zone_id": "z_iot",
                        "ips": ["10.10.0.0/16"],
                        "mac_addresses": ["AA:BB:CC:DD:EE:FF"],
                        "port": "1024",
                        "port_matching_type": "SPECIFIC",
                        "network_id": "net_iot",
                        "port_group_id": "pg_src",
                        "address_group_id": "ag_src",
                    },
                    "destination": {
                        "zone_id": "z_lan",
                        "ips": ["192.168.1.0/24"],
                        "mac_addresses": ["11:22:33:44:55:66"],
                        "port": "443",
                        "port_matching_type": "SPECIFIC",
                        "network_id": "net_lan",
                        "port_group_id": "pg_dst",
                        "address_group_id": "ag_dst",
                    },
                    "connection_state_type": "NEW",
                    "connection_logging": True,
                    "schedule": "work-hours",
                    "match_ip_sec": "MATCH_IPSEC",
                    "index": 500,
                    "predefined": False,
                },
            ]
        )
        policy = policies[0]
        assert policy.source_zone_id == "z_iot"
        assert policy.destination_zone_id == "z_lan"
        assert policy.source_ip_ranges == ("10.10.0.0/16",)
        assert policy.ip_ranges == ("192.168.1.0/24",)
        assert policy.source_mac_addresses == ("AA:BB:CC:DD:EE:FF",)
        assert policy.destination_mac_addresses == ("11:22:33:44:55:66",)
        assert policy.source_port_ranges == ("1024",)
        assert policy.port_ranges == ("443",)
        assert policy.source_network_id == "net_iot"
        assert policy.destination_network_id == "net_lan"
        assert policy.source_port_group_id == "pg_src"
        assert policy.destination_port_group_id == "pg_dst"
        assert policy.source_address_group_id == "ag_src"
        assert policy.destination_address_group_id == "ag_dst"
        assert policy.connection_state_type == "NEW"
        assert policy.connection_logging is True
        assert policy.schedule == "work-hours"
        assert policy.match_ip_sec == "MATCH_IPSEC"
