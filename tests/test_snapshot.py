"""Tests for topology snapshot serialization."""

from __future__ import annotations

from unifi_topology.model.connection import ConnectionInfo
from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.snapshot import (
    _serialize_value,
    client_from_dict,
    client_to_dict,
    connection_info_from_dict,
    connection_info_to_dict,
    device_from_dict,
    device_to_dict,
    edge_from_dict,
    edge_to_dict,
    lldp_entry_from_dict,
    lldp_entry_to_dict,
    port_info_from_dict,
    port_info_to_dict,
    uplink_info_from_dict,
    uplink_info_to_dict,
    wan_info_from_dict,
    wan_info_to_dict,
    wan_interface_from_dict,
    wan_interface_to_dict,
)
from unifi_topology.model.topology import (
    Device,
    Edge,
    PortInfo,
    UplinkInfo,
    WanInfo,
    WanInterface,
)

# --- PortInfo ---


class TestPortInfoSerialization:
    def test_round_trip(self):
        port = PortInfo(
            port_idx=1,
            name="Port 1",
            ifname="eth0",
            speed=1000,
            aggregation_group="lag1",
            port_poe=True,
            poe_enable=True,
            poe_good=True,
            poe_power=15.5,
            native_vlan=10,
            tagged_vlans=(20, 30),
            wan_networkconf_id="WAN",
        )
        data = port_info_to_dict(port)
        restored = port_info_from_dict(data)
        assert restored.port_idx == 1
        assert restored.name == "Port 1"
        assert restored.speed == 1000
        assert restored.poe_power == 15.5
        assert restored.tagged_vlans == (20, 30)

    def test_defaults_for_missing_fields(self):
        data = {"port_idx": 5}
        port = port_info_from_dict(data)
        assert port.port_idx == 5
        assert port.name is None
        assert port.port_poe is False
        assert port.tagged_vlans == ()


# --- UplinkInfo ---


class TestUplinkInfoSerialization:
    def test_round_trip(self):
        uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name="Switch", port=24)
        data = uplink_info_to_dict(uplink)
        restored = uplink_info_from_dict(data)
        assert restored.mac == "aa:bb:cc:dd:ee:ff"
        assert restored.name == "Switch"
        assert restored.port == 24

    def test_handles_none_values(self):
        uplink = UplinkInfo(mac=None, name=None, port=None)
        data = uplink_info_to_dict(uplink)
        restored = uplink_info_from_dict(data)
        assert restored.mac is None


# --- LLDPEntry ---


class TestLLDPEntrySerialization:
    def test_round_trip(self):
        entry = LLDPEntry(
            chassis_id="aa:bb:cc:dd:ee:ff",
            port_id="eth0",
            port_desc="Uplink to Core",
            local_port_name="Port 24",
            local_port_idx=24,
        )
        data = lldp_entry_to_dict(entry)
        restored = lldp_entry_from_dict(data)
        assert restored.chassis_id == "aa:bb:cc:dd:ee:ff"
        assert restored.port_id == "eth0"
        assert restored.port_desc == "Uplink to Core"
        assert restored.local_port_idx == 24

    def test_defaults_for_missing_fields(self):
        data = {"chassis_id": "aa:bb:cc:dd:ee:ff"}
        entry = lldp_entry_from_dict(data)
        assert entry.chassis_id == "aa:bb:cc:dd:ee:ff"
        assert entry.port_id == ""
        assert entry.port_desc is None


# --- WanInterface ---


class TestWanInterfaceSerialization:
    def test_round_trip(self):
        wan = WanInterface(
            port_idx=1,
            link_speed=10000,
            ip_address="203.0.113.1",
            enabled=True,
            label="Fiber",
            isp_speed="1000/1000",
        )
        data = wan_interface_to_dict(wan)
        restored = wan_interface_from_dict(data)
        assert restored.port_idx == 1
        assert restored.link_speed == 10000
        assert restored.ip_address == "203.0.113.1"
        assert restored.enabled is True
        assert restored.label == "Fiber"
        assert restored.isp_speed == "1000/1000"


# --- WanInfo ---


class TestWanInfoSerialization:
    def test_round_trip_single_wan(self):
        wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        info = WanInfo(wan1=wan1, wan2=None)
        data = wan_info_to_dict(info)
        restored = wan_info_from_dict(data)
        assert restored.wan1 is not None
        assert restored.wan1.port_idx == 1
        assert restored.wan2 is None

    def test_round_trip_dual_wan(self):
        wan1 = WanInterface(port_idx=1, link_speed=1000, ip_address="1.2.3.4", enabled=True)
        wan2 = WanInterface(port_idx=9, link_speed=100, ip_address=None, enabled=False)
        info = WanInfo(wan1=wan1, wan2=wan2)
        data = wan_info_to_dict(info)
        restored = wan_info_from_dict(data)
        assert restored.wan1 is not None
        assert restored.wan2 is not None
        assert restored.wan2.port_idx == 9


# --- Device ---


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
        data = device_to_dict(device)
        restored = device_from_dict(data)
        assert restored.name == "switch-1"
        assert restored.mac == "aa:bb:cc:dd:ee:ff"
        assert len(restored.lldp_info) == 1
        assert len(restored.port_table) == 1
        assert restored.poe_ports[1] is True
        assert restored.uplink is not None
        assert restored.uplink.name == "Gateway"

    def test_defaults_for_missing_fields(self):
        data = {"name": "test", "mac": "aa:bb:cc:dd:ee:ff"}
        device = device_from_dict(data)
        assert device.name == "test"
        assert device.lldp_info == []
        assert device.port_table == []
        assert device.poe_ports == {}


# --- Edge ---


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
        data = edge_to_dict(edge)
        restored = edge_from_dict(data)
        assert restored.left == "switch-1"
        assert restored.right == "ap-1"
        assert restored.poe is True
        assert restored.vlans == (1, 10, 20)
        assert restored.is_trunk is True

    def test_defaults_for_missing_fields(self):
        data = {"left": "a", "right": "b"}
        edge = edge_from_dict(data)
        assert edge.left == "a"
        assert edge.poe is False
        assert edge.vlans == ()


# --- Client ---


class TestClientSerialization:
    def test_filters_relevant_keys(self):
        client = {
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "laptop",
            "ip": "192.168.1.100",
            "vlan": 10,
            "is_wired": True,
            "sw_mac": "11:22:33:44:55:66",
            "sw_port": 5,
            "irrelevant_field": "should_be_excluded",
            "another_field": 123,
        }
        data = client_to_dict(client)
        assert "mac" in data
        assert "name" in data
        assert "irrelevant_field" not in data
        assert "another_field" not in data

    def test_from_dict_preserves_all(self):
        data = {"mac": "aa:bb:cc:dd:ee:ff", "name": "test", "custom": "value"}
        client = client_from_dict(data)
        assert client["mac"] == "aa:bb:cc:dd:ee:ff"
        assert client["custom"] == "value"


# --- _serialize_value coverage ---


class TestSerializeValue:
    def test_list_serialization(self):
        result = _serialize_value([1, "two", None])
        assert result == [1, "two", None]

    def test_dict_serialization(self):
        result = _serialize_value({"a": 1, "b": "two"})
        assert result == {"a": 1, "b": "two"}

    def test_nested_dataclass_serialization(self):
        uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name="Switch", port=24)
        result = _serialize_value(uplink)
        assert result == {"mac": "aa:bb:cc:dd:ee:ff", "name": "Switch", "port": 24}

    def test_fallback_to_str(self):
        """Non-primitive, non-container values fall back to str()."""
        result = _serialize_value(object.__class__)
        assert isinstance(result, str)

    def test_nested_list_of_dataclasses(self):
        entries = [
            LLDPEntry(chassis_id="aa:bb", port_id="eth0"),
            LLDPEntry(chassis_id="cc:dd", port_id="eth1"),
        ]
        result = _serialize_value(entries)
        assert len(result) == 2
        assert result[0]["chassis_id"] == "aa:bb"
        assert result[1]["port_id"] == "eth1"

    def test_dict_with_nested_values(self):
        data = {"uplink": UplinkInfo(mac="aa:bb", name="S", port=1)}
        result = _serialize_value(data)
        assert result["uplink"]["mac"] == "aa:bb"


# --- WanInfo null branches ---


class TestWanInfoNullBranches:
    def test_wan_info_both_none(self):
        """Cover line 136: wan1 is None produces result['wan1'] = None."""
        info = WanInfo(wan1=None, wan2=None)
        data = wan_info_to_dict(info)
        assert data["wan1"] is None
        assert data["wan2"] is None

    def test_wan_info_from_dict_with_wan2(self):
        """Cover line 148->150: wan2 is present in data."""
        data = {
            "wan1": None,
            "wan2": {
                "port_idx": 9,
                "link_speed": 100,
                "ip_address": "10.0.0.1",
                "enabled": True,
            },
        }
        restored = wan_info_from_dict(data)
        assert restored.wan1 is None
        assert restored.wan2 is not None
        assert restored.wan2.port_idx == 9
        assert restored.wan2.ip_address == "10.0.0.1"


# --- Device with network_table ---


class TestDeviceNetworkTable:
    def test_device_with_network_table(self):
        """Cover line 175: device.network_table is truthy."""
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
        """When network_table is empty, key is omitted from dict."""
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
        data = device_to_dict(device)
        assert "network_table" not in data


# --- ConnectionInfo ---


class TestConnectionInfoSerialization:
    def test_connection_info_to_dict(self):
        """Cover line 209: connection_info_to_dict."""
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
        """Cover line 214: connection_info_from_dict."""
        data = {
            "signal_dbm": -60,
            "noise_dbm": -90,
            "tx_rate_mbps": 200,
            "rx_rate_mbps": 150,
            "satisfaction": 75,
            "quality": "fair",
        }
        conn = connection_info_from_dict(data)
        assert conn.signal_dbm == -60
        assert conn.noise_dbm == -90
        assert conn.tx_rate_mbps == 200
        assert conn.rx_rate_mbps == 150
        assert conn.satisfaction == 75
        assert conn.quality == "fair"

    def test_connection_info_round_trip(self):
        conn = ConnectionInfo(signal_dbm=-70, quality="fair")
        data = connection_info_to_dict(conn)
        restored = connection_info_from_dict(data)
        assert restored.signal_dbm == conn.signal_dbm
        assert restored.quality == conn.quality

    def test_connection_info_from_dict_with_defaults(self):
        """All fields default to None when missing."""
        data: dict[str, object] = {}
        conn = connection_info_from_dict(data)
        assert conn.signal_dbm is None
        assert conn.noise_dbm is None
        assert conn.quality is None


# --- Edge with connection ---


class TestEdgeWithConnection:
    def test_edge_round_trip_with_connection(self):
        """Cover line 248: edge_from_dict with connection data present."""
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
