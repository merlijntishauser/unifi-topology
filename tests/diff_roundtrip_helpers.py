"""Shared fixtures for diff round-trip tests."""

from __future__ import annotations

from unifi_topology.model.topology import Device, Edge


def sample_device() -> Device:
    return Device(
        name="switch-1",
        model_name="UniFi Switch Pro 24",
        model="USW-Pro-24",
        mac="aa:bb:cc:dd:ee:ff",
        ip="192.168.1.10",
        type="switch",
        lldp_info=[],
        port_table=[],
        poe_ports={},
        uplink=None,
        last_uplink=None,
        version="6.5.0",
    )


def sample_device_2() -> Device:
    return Device(
        name="ap-1",
        model_name="UniFi AP Pro",
        model="UAP-AC-Pro",
        mac="11:22:33:44:55:66",
        ip="192.168.1.20",
        type="ap",
        lldp_info=[],
        port_table=[],
        poe_ports={},
        uplink=None,
        last_uplink=None,
        version="6.5.0",
    )


def sample_client() -> dict[str, object]:
    return {
        "mac": "cc:dd:ee:ff:00:11",
        "name": "laptop-1",
        "ip": "192.168.1.100",
        "vlan": 10,
        "is_wired": True,
        "sw_mac": "aa:bb:cc:dd:ee:ff",
        "sw_port": 5,
    }


def sample_edge() -> Edge:
    return Edge(
        left="switch-1",
        right="ap-1",
        label="Port 24",
        poe=True,
        wireless=False,
        speed=1000,
        channel=None,
        vlans=(1, 10, 20),
        active_vlans=(1, 10),
        is_trunk=True,
    )
