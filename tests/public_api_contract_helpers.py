"""Helpers for public API contract tests."""

from __future__ import annotations


def sample_raw_devices() -> list[dict[str, object]]:
    return [
        {
            "name": "Gateway",
            "model_name": "Gateway",
            "model": "UDM",
            "mac": "aa:aa:aa:aa:aa:aa",
            "ip": "192.168.1.1",
            "type": "gateway",
            "lldp_info": [],
            "port_table": [
                {
                    "port_idx": 1,
                    "name": "Port 1",
                    "ifname": "eth0",
                    "speed": 1000,
                }
            ],
            "network_table": [],
        },
        {
            "name": "Switch",
            "model_name": "Switch",
            "model": "USW-8",
            "mac": "bb:bb:bb:bb:bb:bb",
            "ip": "192.168.1.2",
            "type": "switch",
            "lldp_info": [
                {
                    "chassis_id": "aa:aa:aa:aa:aa:aa",
                    "port_id": "Port 1",
                    "local_port_name": "Port 1",
                }
            ],
            "port_table": [
                {
                    "port_idx": 1,
                    "name": "Port 1",
                    "ifname": "port1",
                    "speed": 1000,
                }
            ],
            "uplink": {
                "uplink_mac": "aa:aa:aa:aa:aa:aa",
                "uplink_device_name": "Gateway",
                "uplink_remote_port": 1,
            },
            "network_table": [],
        },
    ]
