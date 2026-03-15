"""Tests for topology comparison of devices and summary metadata."""

from __future__ import annotations

from tests.diff_compare_helpers import sample_device, sample_device_2
from unifi_topology.model.diff import compare_topologies
from unifi_topology.model.topology import Device


class TestCompareTopologyDevices:
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
