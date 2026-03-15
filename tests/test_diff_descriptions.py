"""Tests for topology diff description text."""

from __future__ import annotations

from tests.diff_compare_helpers import sample_device
from unifi_topology.model.diff import compare_topologies
from unifi_topology.model.topology import Device, Edge, UplinkInfo


class TestDescriptionGeneration:
    def test_device_added_description(self):
        diff = compare_topologies([], [sample_device()])
        assert "switch-1" in diff.events[0].description
        assert "appeared" in diff.events[0].description

    def test_device_removed_description(self):
        diff = compare_topologies([sample_device()], [])
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
        old_device = sample_device()
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
