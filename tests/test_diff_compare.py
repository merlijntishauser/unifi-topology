"""Tests for topology comparison and descriptions."""

from __future__ import annotations

from unifi_topology.model.diff import compare_topologies
from unifi_topology.model.topology import Device, Edge, UplinkInfo


def _sample_device() -> Device:
    return Device(
        name="switch-1",
        model_name="UniFi Switch Pro 24",
        model="USW-Pro-24",
        mac="aa:bb:cc:dd:ee:ff",
        ip="192.168.1.10",
        type="switch",
        lldp_info=[],
        port_table=[],
        poe_ports={},
        uplink=None,
        last_uplink=None,
        version="6.5.0",
    )


def _sample_device_2() -> Device:
    return Device(
        name="ap-1",
        model_name="UniFi AP Pro",
        model="UAP-AC-Pro",
        mac="11:22:33:44:55:66",
        ip="192.168.1.20",
        type="ap",
        lldp_info=[],
        port_table=[],
        poe_ports={},
        uplink=None,
        last_uplink=None,
        version="6.5.0",
    )


def _sample_client() -> dict[str, object]:
    return {
        "mac": "cc:dd:ee:ff:00:11",
        "name": "laptop-1",
        "ip": "192.168.1.100",
        "vlan": 10,
        "is_wired": True,
        "sw_mac": "aa:bb:cc:dd:ee:ff",
        "sw_port": 5,
    }


def _sample_edge() -> Edge:
    return Edge(
        left="switch-1",
        right="ap-1",
        label="Port 24",
        poe=True,
        wireless=False,
        speed=1000,
        channel=None,
        vlans=(1, 10, 20),
        active_vlans=(1, 10),
        is_trunk=True,
    )


class TestCompareTopologies:
    def test_empty_topologies(self):
        diff = compare_topologies([], [])
        assert len(diff.events) == 0
        assert diff.summary == "No changes"

    def test_identical_topologies(self):
        device = _sample_device()
        diff = compare_topologies([device], [device])
        assert len(diff.events) == 0

    def test_device_added(self):
        diff = compare_topologies([], [_sample_device()])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_added"
        assert event.entity_type == "device"
        assert event.name == "switch-1"
        assert "appeared" in event.description

    def test_device_removed(self):
        diff = compare_topologies([_sample_device()], [])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_removed"
        assert event.entity_type == "device"
        assert "disappeared" in event.description

    def test_device_changed_ip(self):
        sample_device = _sample_device()
        new_device = Device(
            name=sample_device.name,
            model_name=sample_device.model_name,
            model=sample_device.model,
            mac=sample_device.mac,
            ip="192.168.1.11",
            type=sample_device.type,
            lldp_info=sample_device.lldp_info,
            port_table=sample_device.port_table,
            poe_ports=sample_device.poe_ports,
            uplink=sample_device.uplink,
            last_uplink=sample_device.last_uplink,
            version=sample_device.version,
        )
        diff = compare_topologies([sample_device], [new_device])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_changed"
        assert "ip" in event.details["changes"]
        assert event.details["changes"]["ip"]["old"] == "192.168.1.10"
        assert event.details["changes"]["ip"]["new"] == "192.168.1.11"

    def test_device_renamed(self):
        sample_device = _sample_device()
        new_device = Device(
            name="switch-main",
            model_name=sample_device.model_name,
            model=sample_device.model,
            mac=sample_device.mac,
            ip=sample_device.ip,
            type=sample_device.type,
            lldp_info=sample_device.lldp_info,
            port_table=sample_device.port_table,
            poe_ports=sample_device.poe_ports,
            uplink=sample_device.uplink,
            last_uplink=sample_device.last_uplink,
            version=sample_device.version,
        )
        diff = compare_topologies([sample_device], [new_device])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_changed"
        assert "renamed" in event.description.lower() or "name" in event.details["changes"]

    def test_client_added(self):
        diff = compare_topologies([], [], old_clients=[], new_clients=[_sample_client()])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_added"
        assert event.entity_type == "client"
        assert "connected" in event.description

    def test_client_removed(self):
        diff = compare_topologies([], [], old_clients=[_sample_client()], new_clients=[])
        assert len(diff.events) == 1
        event = diff.events[0]
        assert event.event_type == "node_removed"
        assert event.entity_type == "client"
        assert "disconnected" in event.description

    def test_client_vlan_changed(self):
        old_client = _sample_client()
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
        diff = compare_topologies([], [], old_edges=[], new_edges=[_sample_edge()])
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "edge_added"
        assert "added" in diff.events[0].description

    def test_edge_removed(self):
        diff = compare_topologies([], [], old_edges=[_sample_edge()], new_edges=[])
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "edge_removed"
        assert "removed" in diff.events[0].description

    def test_edge_changed_speed(self):
        sample_edge = _sample_edge()
        new_edge = Edge(
            left=sample_edge.left,
            right=sample_edge.right,
            label=sample_edge.label,
            poe=sample_edge.poe,
            wireless=sample_edge.wireless,
            speed=10000,
            channel=sample_edge.channel,
            vlans=sample_edge.vlans,
            active_vlans=sample_edge.active_vlans,
            is_trunk=sample_edge.is_trunk,
        )
        diff = compare_topologies([], [], old_edges=[sample_edge], new_edges=[new_edge])
        assert len(diff.events) == 1
        assert diff.events[0].event_type == "edge_changed"
        assert "speed" in diff.events[0].details["changes"]

    def test_multiple_changes(self):
        diff = compare_topologies(
            [_sample_device()],
            [_sample_device(), _sample_device_2()],
            old_clients=[_sample_client()],
            new_clients=[],
        )
        assert len(diff.events) == 2
        event_types = {event.event_type for event in diff.events}
        assert "node_added" in event_types
        assert "node_removed" in event_types

    def test_summary_generation(self):
        diff = compare_topologies([], [_sample_device(), _sample_device_2()])
        assert "2 devices added" in diff.summary

    def test_timestamps_passed_through(self):
        sample_device = _sample_device()
        diff = compare_topologies(
            [sample_device],
            [sample_device],
            old_timestamp="2026-02-05T09:00:00Z",
            new_timestamp="2026-02-05T10:00:00Z",
        )
        assert diff.old_timestamp == "2026-02-05T09:00:00Z"
        assert diff.new_timestamp == "2026-02-05T10:00:00Z"


class TestDescriptionGeneration:
    def test_device_added_description(self):
        diff = compare_topologies([], [_sample_device()])
        assert "switch-1" in diff.events[0].description
        assert "appeared" in diff.events[0].description

    def test_device_removed_description(self):
        diff = compare_topologies([_sample_device()], [])
        assert "switch-1" in diff.events[0].description
        assert "disappeared" in diff.events[0].description

    def test_client_wifi_description(self):
        wifi_client = {
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "phone",
            "is_wired": False,
        }
        diff = compare_topologies([], [], old_clients=[], new_clients=[wifi_client])
        assert "WiFi" in diff.events[0].description

    def test_client_wired_description(self):
        wired_client = {
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "desktop",
            "is_wired": True,
        }
        diff = compare_topologies([], [], old_clients=[], new_clients=[wired_client])
        assert "wired" in diff.events[0].description

    def test_device_changed_uplink_mac(self):
        old_device = Device(
            name="switch-1",
            model_name="Switch",
            model="USW",
            mac="aa:bb:cc:dd:ee:ff",
            ip="192.168.1.10",
            type="switch",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=UplinkInfo(mac="11:11:11:11:11:11", name="Old Gateway", port=1),
            last_uplink=None,
            version="6.5.0",
        )
        new_device = Device(
            name="switch-1",
            model_name="Switch",
            model="USW",
            mac="aa:bb:cc:dd:ee:ff",
            ip="192.168.1.10",
            type="switch",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=UplinkInfo(mac="22:22:22:22:22:22", name="New Gateway", port=1),
            last_uplink=None,
            version="6.5.0",
        )
        diff = compare_topologies([old_device], [new_device])
        assert len(diff.events) == 1
        assert "uplink changed" in diff.events[0].description

    def test_device_changed_uplink_port(self):
        old_device = Device(
            name="switch-1",
            model_name="Switch",
            model="USW",
            mac="aa:bb:cc:dd:ee:ff",
            ip="192.168.1.10",
            type="switch",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=UplinkInfo(mac="11:11:11:11:11:11", name="Gateway", port=1),
            last_uplink=None,
            version="6.5.0",
        )
        new_device = Device(
            name="switch-1",
            model_name="Switch",
            model="USW",
            mac="aa:bb:cc:dd:ee:ff",
            ip="192.168.1.10",
            type="switch",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=UplinkInfo(mac="11:11:11:11:11:11", name="Gateway", port=5),
            last_uplink=None,
            version="6.5.0",
        )
        diff = compare_topologies([old_device], [new_device])
        assert len(diff.events) == 1
        assert "moved to port" in diff.events[0].description

    def test_device_changed_generic_property(self):
        old_device = Device(
            name="switch-1",
            model_name="Switch",
            model="USW",
            mac="aa:bb:cc:dd:ee:ff",
            ip="192.168.1.10",
            type="switch",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=None,
            last_uplink=None,
            version="6.5.0",
        )
        new_device = Device(
            name="switch-1",
            model_name="Switch",
            model="USW",
            mac="aa:bb:cc:dd:ee:ff",
            ip="192.168.1.10",
            type="switch",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=None,
            last_uplink=None,
            version="7.0.0",
        )
        diff = compare_topologies([old_device], [new_device])
        assert len(diff.events) == 1
        assert "version changed" in diff.events[0].description

    def test_device_changed_multiple_properties(self):
        old_device = _sample_device()
        new_device = Device(
            name="switch-main",
            model_name="Switch",
            model="USW",
            mac="aa:bb:cc:dd:ee:ff",
            ip="192.168.1.99",
            type="switch",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=None,
            last_uplink=None,
            version="7.0.0",
        )
        diff = compare_topologies([old_device], [new_device])
        assert len(diff.events) == 1
        assert "changed" in diff.events[0].description
        assert "properties" in diff.events[0].description

    def test_client_changed_ip(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "ip": "192.168.1.100",
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "ip": "192.168.1.200",
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "IP changed" in diff.events[0].description

    def test_client_changed_uplink_mac(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "sw_mac": "11:11:11:11:11:11",
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "sw_mac": "22:22:22:22:22:22",
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "moved to different device" in diff.events[0].description

    def test_client_changed_uplink_port(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "sw_port": 5,
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "sw_port": 10,
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "moved to port" in diff.events[0].description

    def test_client_changed_generic_property(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "channel": 36,
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "channel": 149,
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "channel changed" in diff.events[0].description

    def test_client_changed_multiple_properties(self):
        old_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "ip": "192.168.1.100",
            "channel": 36,
        }
        new_client = {
            "mac": "cc:dd:ee:ff:00:11",
            "name": "laptop",
            "ip": "192.168.1.200",
            "channel": 149,
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "changed" in diff.events[0].description
        assert "properties" in diff.events[0].description

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

    def test_client_with_no_name_uses_mac(self):
        old_client: dict[str, object] = {
            "mac": "cc:dd:ee:ff:00:11",
            "ip": "192.168.1.100",
        }
        new_client: dict[str, object] = {
            "mac": "cc:dd:ee:ff:00:11",
            "ip": "192.168.1.200",
        }
        diff = compare_topologies([], [], old_clients=[old_client], new_clients=[new_client])
        assert len(diff.events) == 1
        assert "cc:dd:ee:ff:00:11" in diff.events[0].description
