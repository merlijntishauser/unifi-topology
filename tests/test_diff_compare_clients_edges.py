"""Tests for topology comparison of clients and edges."""

from __future__ import annotations

from tests.diff_compare_helpers import sample_client, sample_device, sample_device_2, sample_edge
from unifi_topology.model.diff import compare_topologies
from unifi_topology.model.topology import Edge


class TestCompareTopologyClientsAndEdges:
    def test_client_added(self):
        diff = compare_topologies([], [], old_clients=[], new_clients=[sample_client()])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_added"
        assert event.entity_type == "client"
        assert "connected" in event.description

    def test_client_removed(self):
        diff = compare_topologies([], [], old_clients=[sample_client()], new_clients=[])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_removed"
        assert event.entity_type == "client"
        assert "disconnected" in event.description

    def test_client_vlan_changed(self):
        old_client = sample_client()
        new_client = dict(old_client)
        new_client["vlan"] = 20
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_changed"
        assert event.entity_type == "client"
        assert "VLAN" in event.description
        assert event.details["changes"]["vlan"]["old"] == 10
        assert event.details["changes"]["vlan"]["new"] == 20

    def test_edge_added(self):
        diff = compare_topologies([], [], old_edges=[], new_edges=[sample_edge()])
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "edge_added"
        assert "added" in diff.events[0].description

    def test_edge_removed(self):
        diff = compare_topologies([], [], old_edges=[sample_edge()], new_edges=[])
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "edge_removed"
        assert "removed" in diff.events[0].description

    def test_edge_changed_speed(self):
        old_edge = sample_edge()
        new_edge = Edge(
            left=old_edge.left,
            right=old_edge.right,
            label=old_edge.label,
            poe=old_edge.poe,
            wireless=old_edge.wireless,
            speed=10000,
            channel=old_edge.channel,
            vlans=old_edge.vlans,
            active_vlans=old_edge.active_vlans,
            is_trunk=old_edge.is_trunk,
        )
        diff = compare_topologies([], [], old_edges=[old_edge], new_edges=[new_edge])
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "edge_changed"
        assert "speed" in diff.events[0].details["changes"]

    def test_multiple_changes(self):
        diff = compare_topologies(
            [sample_device()],
            [sample_device(), sample_device_2()],
            old_clients=[sample_client()],
            new_clients=[],
        )
        assert len(diff.events) == 2
        event_types = {event.event_type for event in diff.events}
        assert "node_added" in event_types
        assert "node_removed" in event_types

    def test_edge_added_has_edge_entity_type(self):
        diff = compare_topologies([], [], old_edges=[], new_edges=[sample_edge()])
        assert diff.events[0].entity_type == "edge"

    def test_edge_events_excluded_by_device_filter(self):
        diff = compare_topologies([], [], old_edges=[], new_edges=[sample_edge()])
        assert diff.filter(entity_types={"device"}).events == []
        assert len(diff.filter(entity_types={"edge"}).events) == 1

    def test_signal_only_change_is_not_reported(self):
        old_client = sample_client()
        old_client["signal"] = -50
        new_client = dict(old_client)
        new_client["signal"] = -55
        new_client["satisfaction"] = 90
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert diff.events == []


def test_client_vlan_zero_is_not_coalesced_away():
    from unifi_topology.model.diff import _client_uplink_port_value, _client_vlan_value

    assert _client_vlan_value({"vlan": 0, "vlan_id": 99}) == 0
    assert _client_uplink_port_value({"sw_port": 0, "uplink_remote_port": 5}) == 0


def test_devices_with_empty_mac_do_not_collide():
    import dataclasses

    from unifi_topology.model.diff import _device_key

    dev_a = dataclasses.replace(sample_device(), mac="", name="A")
    dev_b = dataclasses.replace(sample_device(), mac="", name="B")
    assert _device_key(dev_a) is None
    assert _device_key(dev_b) is None
    # Two empty-mac devices must not be compared against each other.
    diff = compare_topologies([dev_a], [dev_b])
    assert diff.events == []
