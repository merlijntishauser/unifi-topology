"""Tests for topology diff container filtering APIs."""

from __future__ import annotations

from unifi_topology.model.diff import TopologyChangeEvent, TopologyDiff


class TestTopologyDiffFiltering:
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
