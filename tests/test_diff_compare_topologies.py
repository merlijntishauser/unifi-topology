"""Tests for topology comparison results."""

from __future__ import annotations

from tests.diff_compare_helpers import (
    sample_client,
    sample_device,
    sample_device_2,
    sample_edge,
)
from unifi_topology.model.diff import compare_topologies
from unifi_topology.model.topology import Device, Edge


class TestCompareTopologies:
    def test_empty_topologies(self):
        diff = compare_topologies([], [])
        assert len(diff.events) == 0
        assert diff.summary == "No changes"

    def test_identical_topologies(self):
        device = sample_device()
        diff = compare_topologies([device], [device])
        assert len(diff.events) == 0

    def test_device_added(self):
        diff = compare_topologies([], [sample_device()])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_added"
        assert event.entity_type == "device"
        assert event.name == "switch-1"
        assert "appeared" in event.description

    def test_device_removed(self):
        diff = compare_topologies([sample_device()], [])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_removed"
        assert event.entity_type == "device"
        assert "disappeared" in event.description

    def test_device_changed_ip(self):
        old_device = sample_device()
        new_device = Device(
            name=old_device.name,
            model_name=old_device.model_name,
            model=old_device.model,
            mac=old_device.mac,
            ip="192.168.1.11",
            type=old_device.type,
            lldp_info=old_device.lldp_info,
            port_table=old_device.port_table,
            poe_ports=old_device.poe_ports,
            uplink=old_device.uplink,
            last_uplink=old_device.last_uplink,
            version=old_device.version,
        )
        diff = compare_topologies([old_device], [new_device])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_changed"
        assert "ip" in event.details["changes"]
        assert event.details["changes"]["ip"]["old"] == "192.168.1.10"
        assert event.details["changes"]["ip"]["new"] == "192.168.1.11"

    def test_device_renamed(self):
        old_device = sample_device()
        new_device = Device(
            name="switch-main",
            model_name=old_device.model_name,
            model=old_device.model,
            mac=old_device.mac,
            ip=old_device.ip,
            type=old_device.type,
            lldp_info=old_device.lldp_info,
            port_table=old_device.port_table,
            poe_ports=old_device.poe_ports,
            uplink=old_device.uplink,
            last_uplink=old_device.last_uplink,
            version=old_device.version,
        )
        diff = compare_topologies([old_device], [new_device])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_changed"
        assert "renamed" in event.description.lower() or "name" in event.details["changes"]

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

    def test_summary_generation(self):
        diff = compare_topologies([], [sample_device(), sample_device_2()])
        assert "2 devices added" in diff.summary

    def test_timestamps_passed_through(self):
        device = sample_device()
        diff = compare_topologies(
            [device],
            [device],
            old_timestamp="2026-02-05T09:00:00Z",
            new_timestamp="2026-02-05T10:00:00Z",
        )
        assert diff.old_timestamp == "2026-02-05T09:00:00Z"
        assert diff.new_timestamp == "2026-02-05T10:00:00Z"
