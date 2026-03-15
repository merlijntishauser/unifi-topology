"""Tests for Topology.diff()."""

from __future__ import annotations

from tests.diff_roundtrip_helpers import sample_client, sample_device, sample_device_2
from unifi_topology.model.topology import Topology


class TestTopologyDiffMethod:
    def test_diff_method(self):
        old = Topology(devices=[sample_device()])
        new = Topology(devices=[sample_device(), sample_device_2()])
        diff = old.diff(new)
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "node_added"
        assert diff.events[0].name == "ap-1"

    def test_diff_method_with_clients(self):
        device = sample_device()
        client = sample_client()
        old = Topology(devices=[device], clients=[client])
        new = Topology(devices=[device], clients=[])
        diff = old.diff(new)
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "node_removed"
        assert diff.events[0].entity_type == "client"

    def test_diff_method_timestamps(self):
        device = sample_device()
        old = Topology(devices=[device], timestamp="2026-02-05T09:00:00Z")
        new = Topology(devices=[device], timestamp="2026-02-05T10:00:00Z")
        diff = old.diff(new)
        assert diff.old_timestamp == "2026-02-05T09:00:00Z"
        assert diff.new_timestamp == "2026-02-05T10:00:00Z"
