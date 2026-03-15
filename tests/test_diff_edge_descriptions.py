"""Tests for edge-related topology diff descriptions."""

from __future__ import annotations

from unifi_topology.model.diff import compare_topologies
from unifi_topology.model.topology import Edge


class TestEdgeDescriptions:
    def test_edge_changed_poe(self):
        old_edge = Edge(
            left="switch-1",
            right="ap-1",
            label="Port 24",
            poe=False,
            wireless=False,
            speed=1000,
            channel=None,
            vlans=(1,),
            active_vlans=(1,),
            is_trunk=False,
        )
        new_edge = Edge(
            left="switch-1",
            right="ap-1",
            label="Port 24",
            poe=True,
            wireless=False,
            speed=1000,
            channel=None,
            vlans=(1,),
            active_vlans=(1,),
            is_trunk=False,
        )
        diff = compare_topologies([], [], old_edges=[old_edge], new_edges=[new_edge])
        assert len(diff.events) == 1
        assert "PoE enabled" in diff.events[0].description

    def test_edge_changed_poe_disabled(self):
        old_edge = Edge(
            left="switch-1",
            right="ap-1",
            label="Port 24",
            poe=True,
            wireless=False,
            speed=1000,
        )
        new_edge = Edge(
            left="switch-1",
            right="ap-1",
            label="Port 24",
            poe=False,
            wireless=False,
            speed=1000,
        )
        diff = compare_topologies([], [], old_edges=[old_edge], new_edges=[new_edge])
        assert len(diff.events) == 1
        assert "PoE disabled" in diff.events[0].description
