"""Tests for diff-related serialization round trips."""

from __future__ import annotations

import json

from tests.diff_roundtrip_helpers import sample_client, sample_device, sample_edge
from unifi_topology.model.snapshot import (
    device_from_dict,
    device_to_dict,
    edge_from_dict,
    edge_to_dict,
)
from unifi_topology.model.topology import Topology


class TestSerializationRoundTrip:
    def test_device_round_trip(self):
        device = sample_device()
        data = device_to_dict(device)
        restored = device_from_dict(data)
        assert restored.name == device.name
        assert restored.mac == device.mac
        assert restored.ip == device.ip
        assert restored.model == device.model
        assert restored.type == device.type
        assert restored.version == device.version

    def test_edge_round_trip(self):
        edge = sample_edge()
        data = edge_to_dict(edge)
        restored = edge_from_dict(data)
        assert restored.left == edge.left
        assert restored.right == edge.right
        assert restored.poe == edge.poe
        assert restored.speed == edge.speed
        assert restored.vlans == edge.vlans
        assert restored.is_trunk == edge.is_trunk

    def test_topology_round_trip(self):
        device = sample_device()
        client = sample_client()
        edge = sample_edge()
        topology = Topology(
            devices=[device],
            clients=[client],
            edges=[edge],
            timestamp="2026-02-05T10:00:00Z",
        )
        data = topology.to_dict()
        restored = Topology.from_dict(data)
        assert len(restored.devices) == 1
        assert restored.devices[0].name == device.name
        assert len(restored.clients) == 1
        assert restored.clients[0]["mac"] == client["mac"]
        assert len(restored.edges) == 1
        assert restored.edges[0].left == edge.left
        assert restored.timestamp == "2026-02-05T10:00:00Z"

    def test_topology_json_round_trip(self):
        device = sample_device()
        edge = sample_edge()
        topology = Topology(
            devices=[device],
            edges=[edge],
            timestamp="2026-02-05T10:00:00Z",
        )
        json_str = json.dumps(topology.to_dict())
        data = json.loads(json_str)
        restored = Topology.from_dict(data)
        assert restored.devices[0].mac == device.mac
