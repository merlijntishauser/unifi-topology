"""Tests for topology diff event APIs."""

from __future__ import annotations

import json

from unifi_topology.model.diff import TopologyChangeEvent


class TestTopologyChangeEvent:
    def test_to_dict(self):
        event = TopologyChangeEvent(
            event_type="node_added",
            entity_type="device",
            identifier="aa:bb:cc:dd:ee:ff",
            name="switch-1",
            description="Device 'switch-1' appeared on network",
            details={"ip": "192.168.1.10"},
            timestamp="2026-02-05T10:00:00Z",
        )

        result = event.to_dict()

        assert result["event_type"] == "node_added"
        assert result["entity_type"] == "device"
        assert result["identifier"] == "aa:bb:cc:dd:ee:ff"
        assert result["name"] == "switch-1"
        assert result["description"] == "Device 'switch-1' appeared on network"
        assert result["details"]["ip"] == "192.168.1.10"
        assert result["timestamp"] == "2026-02-05T10:00:00Z"

    def test_to_dict_is_json_serializable(self):
        event = TopologyChangeEvent(
            event_type="node_changed",
            entity_type="client",
            identifier="cc:dd:ee:ff:00:11",
            name="laptop",
            description="Client changed",
            details={"changes": {"vlan": {"old": 10, "new": 20}}},
        )

        json_str = json.dumps(event.to_dict())

        assert "node_changed" in json_str
