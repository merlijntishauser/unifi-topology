"""Tests for snapshot serialization of Device objects."""

from __future__ import annotations

from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.snapshot import device_from_dict, device_to_dict
from unifi_topology.model.topology import Device, PortInfo, UplinkInfo


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


def test_in_gateway_mode_survives_round_trip():
    for mode in (True, False, None):
        device = Device(
            name="ux",
            model_name="",
            model="",
            mac="aa:bb:cc:dd:ee:ff",
            ip="",
            type="uxg",
            lldp_info=[],
            port_table=[],
            poe_ports={},
            uplink=None,
            last_uplink=None,
            version="",
            in_gateway_mode=mode,
        )
        restored = device_from_dict(device_to_dict(device))
        assert restored.in_gateway_mode is mode


def test_device_round_trip_preserves_all_fields():
    import dataclasses

    device = Device(
        name="ux",
        model_name="M",
        model="m",
        mac="aa:bb:cc:dd:ee:ff",
        ip="10.0.0.1",
        type="uxg",
        lldp_info=[],
        port_table=[],
        poe_ports={},
        uplink=None,
        last_uplink=None,
        version="1.2.3",
        in_gateway_mode=False,
        network_table=[],
        public_ip="1.2.3.4",
    )
    restored = device_from_dict(device_to_dict(device))
    for field in dataclasses.fields(Device):
        assert getattr(restored, field.name) == getattr(device, field.name), field.name
