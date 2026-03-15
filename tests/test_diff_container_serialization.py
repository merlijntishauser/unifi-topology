"""Tests for topology diff container serialization APIs."""

from __future__ import annotations

import json

from unifi_topology.model.diff import TopologyChangeEvent, TopologyDiff


class TestTopologyDiffSerialization:
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

        parsed = json.loads(diff.to_json())

        assert len(parsed["events"]) == 1
        assert parsed["summary"] == "1 device added"
