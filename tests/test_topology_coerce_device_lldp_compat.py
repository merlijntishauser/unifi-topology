"""Compatibility-focused tests for device LLDP coercion behavior."""

from __future__ import annotations

import pytest

from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.topology_coerce import coerce_device


def test_coerce_device_uses_lldp_fallback():
    class DeviceWithLldp:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = None
        lldp = [LLDPEntry("bb", "1")]
        port_table = []

    device = coerce_device(DeviceWithLldp())
    assert device.lldp_info[0].chassis_id == "bb"


def test_coerce_device_uses_lldp_table_fallback():
    class DeviceWithLldpTable:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = None
        lldp = None
        lldp_table = [LLDPEntry("bb", "1")]
        port_table = []

    device = coerce_device(DeviceWithLldpTable())
    assert device.lldp_info[0].chassis_id == "bb"


@pytest.fixture()
def device_with_uplink_no_lldp():
    class MissingLldpWithUplink:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = None
        lldp = None
        uplink = {"uplink_mac": "bb", "uplink_device_name": "Gateway", "uplink_remote_port": 1}
        port_table = []

    return MissingLldpWithUplink()


def test_coerce_device_allows_uplink_when_lldp_missing(device_with_uplink_no_lldp):
    assert coerce_device(device_with_uplink_no_lldp).lldp_info == []


def test_coerce_device_tracks_poe_false_when_power_invalid():
    class DeviceWithPort:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = [LLDPEntry("bb", "1")]
        port_table = [{"port_idx": 1, "poe_power": "bad"}]

    assert coerce_device(DeviceWithPort()).poe_ports[1] is False
