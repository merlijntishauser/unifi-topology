"""Tests for diff serialization and Topology.diff()."""

from __future__ import annotations

import json

from unifi_topology.model.snapshot import (
    device_from_dict,
    device_to_dict,
    edge_from_dict,
    edge_to_dict,
)
from unifi_topology.model.topology import Device, Edge, Topology


def _sample_device() -> Device:
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


def _sample_device_2() -> Device:
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


def _sample_client() -> dict[str, object]:
    return {
        "mac": "cc:dd:ee:ff:00:11",
        "name": "laptop-1",
        "ip": "192.168.1.100",
        "vlan": 10,
        "is_wired": True,
        "sw_mac": "aa:bb:cc:dd:ee:ff",
        "sw_port": 5,
    }


def _sample_edge() -> Edge:
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


class TestSerializationRoundTrip:
    def test_device_round_trip(self):
        sample_device = _sample_device()
        data = device_to_dict(sample_device)
        restored = device_from_dict(data)
        assert restored.name == sample_device.name
        assert restored.mac == sample_device.mac
        assert restored.ip == sample_device.ip
        assert restored.model == sample_device.model
        assert restored.type == sample_device.type
        assert restored.version == sample_device.version

    def test_edge_round_trip(self):
        sample_edge = _sample_edge()
        data = edge_to_dict(sample_edge)
        restored = edge_from_dict(data)
        assert restored.left == sample_edge.left
        assert restored.right == sample_edge.right
        assert restored.poe == sample_edge.poe
        assert restored.speed == sample_edge.speed
        assert restored.vlans == sample_edge.vlans
        assert restored.is_trunk == sample_edge.is_trunk

    def test_topology_round_trip(self):
        sample_device = _sample_device()
        sample_client = _sample_client()
        sample_edge = _sample_edge()
        topology = Topology(
            devices=[sample_device],
            clients=[sample_client],
            edges=[sample_edge],
            timestamp="2026-02-05T10:00:00Z",
        )
        data = topology.to_dict()
        restored = Topology.from_dict(data)
        assert len(restored.devices) == 1
        assert restored.devices[0].name == sample_device.name
        assert len(restored.clients) == 1
        assert restored.clients[0]["mac"] == sample_client["mac"]
        assert len(restored.edges) == 1
        assert restored.edges[0].left == sample_edge.left
        assert restored.timestamp == "2026-02-05T10:00:00Z"

    def test_topology_json_round_trip(self):
        sample_device = _sample_device()
        sample_edge = _sample_edge()
        topology = Topology(
            devices=[sample_device],
            edges=[sample_edge],
            timestamp="2026-02-05T10:00:00Z",
        )
        json_str = json.dumps(topology.to_dict())
        data = json.loads(json_str)
        restored = Topology.from_dict(data)
        assert restored.devices[0].mac == sample_device.mac


class TestTopologyDiffMethod:
    def test_diff_method(self):
        old = Topology(devices=[_sample_device()])
        new = Topology(devices=[_sample_device(), _sample_device_2()])
        diff = old.diff(new)
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "node_added"
        assert diff.events[0].name == "ap-1"

    def test_diff_method_with_clients(self):
        sample_device = _sample_device()
        sample_client = _sample_client()
        old = Topology(devices=[sample_device], clients=[sample_client])
        new = Topology(devices=[sample_device], clients=[])
        diff = old.diff(new)
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "node_removed"
        assert diff.events[0].entity_type == "client"

    def test_diff_method_timestamps(self):
        sample_device = _sample_device()
        old = Topology(devices=[sample_device], timestamp="2026-02-05T09:00:00Z")
        new = Topology(devices=[sample_device], timestamp="2026-02-05T10:00:00Z")
        diff = old.diff(new)
        assert diff.old_timestamp == "2026-02-05T09:00:00Z"
        assert diff.new_timestamp == "2026-02-05T10:00:00Z"
