"""Tests for diff event and container APIs."""

from __future__ import annotations

import json

from unifi_topology.model.diff import TopologyChangeEvent, TopologyDiff


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


class TestTopologyDiff:
    def test_empty_diff(self):
        diff = TopologyDiff()
        assert diff.events == []
        assert diff.summary == ""

    def test_to_dict(self):
        event = TopologyChangeEvent(
            event_type="node_added",
            entity_type="device",
            identifier="aa:bb:cc:dd:ee:ff",
            name="switch-1",
            description="Device added",
        )
        diff = TopologyDiff(
            events=[event],
            old_timestamp="2026-02-05T09:00:00Z",
            new_timestamp="2026-02-05T10:00:00Z",
            summary="1 device added",
        )
        result = diff.to_dict()
        assert len(result["events"]) == 1
        assert result["old_timestamp"] == "2026-02-05T09:00:00Z"
        assert result["new_timestamp"] == "2026-02-05T10:00:00Z"
        assert result["summary"] == "1 device added"

    def test_to_json(self):
        diff = TopologyDiff(
            events=[
                TopologyChangeEvent(
                    event_type="node_added",
                    entity_type="device",
                    identifier="aa:bb:cc:dd:ee:ff",
                    name="switch-1",
                    description="Device added",
                )
            ],
            summary="1 device added",
        )
        json_str = diff.to_json()
        parsed = json.loads(json_str)
        assert len(parsed["events"]) == 1
        assert parsed["summary"] == "1 device added"

    def test_filter_by_event_type(self):
        events = [
            TopologyChangeEvent(
                event_type="node_added",
                entity_type="device",
                identifier="a",
                name="a",
                description="",
            ),
            TopologyChangeEvent(
                event_type="node_removed",
                entity_type="device",
                identifier="b",
                name="b",
                description="",
            ),
            TopologyChangeEvent(
                event_type="edge_added",
                entity_type="device",
                identifier="c",
                name=None,
                description="",
            ),
        ]
        diff = TopologyDiff(events=events, summary="test")
        filtered = diff.filter(event_types={"node_added", "node_removed"})
        assert len(filtered.events) == 2
        assert all(e.event_type in {"node_added", "node_removed"} for e in filtered.events)

    def test_filter_by_entity_type(self):
        events = [
            TopologyChangeEvent(
                event_type="node_added",
                entity_type="device",
                identifier="a",
                name="a",
                description="",
            ),
            TopologyChangeEvent(
                event_type="node_added",
                entity_type="client",
                identifier="b",
                name="b",
                description="",
            ),
        ]
        diff = TopologyDiff(events=events, summary="test")
        filtered = diff.filter(entity_types={"client"})
        assert len(filtered.events) == 1
        assert filtered.events[0].entity_type == "client"
