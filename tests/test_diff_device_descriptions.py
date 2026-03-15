"""Tests for device-related topology diff descriptions."""

from __future__ import annotations

from tests.diff_compare_helpers import sample_device
from unifi_topology.model.diff import compare_topologies
from unifi_topology.model.topology import Device, UplinkInfo


def _device(*, uplink: UplinkInfo | None = None, version: str = "6.5.0") -> Device:
    return Device(
        name="switch-1",
        model_name="Switch",
        model="USW",
        mac="aa:bb:cc:dd:ee:ff",
        ip="192.168.1.10",
        type="switch",
        lldp_info=[],
        port_table=[],
        poe_ports={},
        uplink=uplink,
        last_uplink=None,
        version=version,
    )


class TestDeviceDescriptions:
    def test_device_added_description(self):
        diff = compare_topologies([], [sample_device()])
        assert "switch-1" in diff.events[0].description
        assert "appeared" in diff.events[0].description

    def test_device_removed_description(self):
        diff = compare_topologies([sample_device()], [])
        assert "switch-1" in diff.events[0].description
        assert "disappeared" in diff.events[0].description

    def test_device_changed_uplink_mac(self):
        old_device = _device(uplink=UplinkInfo(mac="11:11:11:11:11:11", name="Old Gateway", port=1))
        new_device = _device(uplink=UplinkInfo(mac="22:22:22:22:22:22", name="New Gateway", port=1))
        diff = compare_topologies([old_device], [new_device])
        assert len(diff.events) == 1
        assert "uplink changed" in diff.events[0].description

    def test_device_changed_uplink_port(self):
        old_device = _device(uplink=UplinkInfo(mac="11:11:11:11:11:11", name="Gateway", port=1))
        new_device = _device(uplink=UplinkInfo(mac="11:11:11:11:11:11", name="Gateway", port=5))
        diff = compare_topologies([old_device], [new_device])
        assert len(diff.events) == 1
        assert "moved to port" in diff.events[0].description

    def test_device_changed_generic_property(self):
        old_device = _device()
        new_device = _device(version="7.0.0")
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
