"""Tests for fully populated nested firewall policy normalization."""

import pytest

from unifi_topology.model.firewall_coerce import normalize_firewall_policies

pytestmark = pytest.mark.unit


def test_full_v2_nested_entry():
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
