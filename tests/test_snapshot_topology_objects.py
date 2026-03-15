"""Tests for snapshot serialization of topology objects."""

from __future__ import annotations

from unifi_topology.model.connection import ConnectionInfo
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.snapshot import (
    connection_info_from_dict,
    connection_info_to_dict,
    device_from_dict,
    device_to_dict,
    edge_from_dict,
    edge_to_dict,
)
from unifi_topology.model.topology import Device, Edge, PortInfo, UplinkInfo


class TestDeviceSerialization:
    def test_round_trip(self):
        device = Device(
            name="switch-1",
            model_name="UniFi Switch Pro 24",
            model="USW-Pro-24",
            mac="aa:bb:cc:dd:ee:ff",
            ip="192.168.1.10",
            type="switch",
            lldp_info=[LLDPEntry(chassis_id="11:22:33:44:55:66", port_id="eth0")],
            port_table=[
                PortInfo(
                    port_idx=1,
                    name="Port 1",
                    ifname="eth0",
                    speed=1000,
                    aggregation_group=None,
                    port_poe=True,
                    poe_enable=True,
                    poe_good=True,
                    poe_power=10.0,
                )
            ],
            poe_ports={1: True, 2: False},
            uplink=UplinkInfo(mac="00:11:22:33:44:55", name="Gateway", port=1),
            last_uplink=None,
            version="6.5.0",
        )
        restored = device_from_dict(device_to_dict(device))
        assert restored.name == "switch-1"
        assert restored.mac == "aa:bb:cc:dd:ee:ff"
        assert len(restored.lldp_info) == 1
        assert len(restored.port_table) == 1
        assert restored.poe_ports[1] is True
        assert restored.uplink is not None
        assert restored.uplink.name == "Gateway"

    def test_defaults_for_missing_fields(self):
        device = device_from_dict({"name": "test", "mac": "aa:bb:cc:dd:ee:ff"})
        assert device.name == "test"
        assert device.lldp_info == []
        assert device.port_table == []
        assert device.poe_ports == {}


class TestEdgeSerialization:
    def test_round_trip(self):
        edge = Edge(
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
        restored = edge_from_dict(edge_to_dict(edge))
        assert restored.left == "switch-1"
        assert restored.right == "ap-1"
        assert restored.poe is True
        assert restored.vlans == (1, 10, 20)
        assert restored.is_trunk is True

    def test_defaults_for_missing_fields(self):
        edge = edge_from_dict({"left": "a", "right": "b"})
        assert edge.left == "a"
        assert edge.poe is False
        assert edge.vlans == ()


class TestDeviceNetworkTable:
    def test_device_with_network_table(self):
        device = Device(
            name="gateway",
            model_name="UniFi Dream Machine",
            model="UDM",
            mac="aa:bb:cc:dd:ee:ff",
            ip="192.168.1.1",
            type="ugw",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=None,
            last_uplink=None,
            version="3.0.0",
            network_table=[{"name": "LAN", "subnet": "192.168.1.0/24"}],
        )
        data = device_to_dict(device)
        assert "network_table" in data
        assert data["network_table"] == [{"name": "LAN", "subnet": "192.168.1.0/24"}]

    def test_device_without_network_table(self):
        device = Device(
            name="switch",
            model_name="Switch",
            model="USW",
            mac="11:22:33:44:55:66",
            ip="192.168.1.2",
            type="switch",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=None,
            last_uplink=None,
            version="6.0",
            network_table=[],
        )
        assert "network_table" not in device_to_dict(device)


class TestConnectionInfoSerialization:
    def test_connection_info_to_dict(self):
        conn = ConnectionInfo(
            signal_dbm=-55,
            noise_dbm=-95,
            tx_rate_mbps=400,
            rx_rate_mbps=300,
            satisfaction=85,
            quality="good",
        )
        data = connection_info_to_dict(conn)
        assert data["signal_dbm"] == -55
        assert data["noise_dbm"] == -95
        assert data["tx_rate_mbps"] == 400
        assert data["rx_rate_mbps"] == 300
        assert data["satisfaction"] == 85
        assert data["quality"] == "good"

    def test_connection_info_from_dict(self):
        conn = connection_info_from_dict(
            {
                "signal_dbm": -60,
                "noise_dbm": -90,
                "tx_rate_mbps": 200,
                "rx_rate_mbps": 150,
                "satisfaction": 75,
                "quality": "fair",
            }
        )
        assert conn.signal_dbm == -60
        assert conn.noise_dbm == -90
        assert conn.tx_rate_mbps == 200
        assert conn.rx_rate_mbps == 150
        assert conn.satisfaction == 75
        assert conn.quality == "fair"

    def test_connection_info_round_trip(self):
        conn = ConnectionInfo(signal_dbm=-70, quality="fair")
        restored = connection_info_from_dict(connection_info_to_dict(conn))
        assert restored.signal_dbm == conn.signal_dbm
        assert restored.quality == conn.quality

    def test_connection_info_from_dict_with_defaults(self):
        conn = connection_info_from_dict({})
        assert conn.signal_dbm is None
        assert conn.noise_dbm is None
        assert conn.quality is None


class TestEdgeWithConnection:
    def test_edge_round_trip_with_connection(self):
        conn = ConnectionInfo(
            signal_dbm=-50,
            noise_dbm=-90,
            tx_rate_mbps=866,
            rx_rate_mbps=400,
            satisfaction=95,
            quality="excellent",
        )
        edge = Edge(
            left="ap-1",
            right="client-1",
            label="WiFi",
            poe=False,
            wireless=True,
            speed=None,
            channel=36,
            vlans=(),
            active_vlans=(),
            is_trunk=False,
            connection=conn,
        )
        data = edge_to_dict(edge)
        assert data["connection"] is not None
        assert data["connection"]["signal_dbm"] == -50
        restored = edge_from_dict(data)
        assert restored.connection is not None
        assert restored.connection.signal_dbm == -50
        assert restored.connection.quality == "excellent"
        assert restored.wireless is True
        assert restored.channel == 36
