"""Tests for snapshot serialization of PortInfo and UplinkInfo."""

from __future__ import annotations

from unifi_topology.model.snapshot import (
    port_info_from_dict,
    port_info_to_dict,
    uplink_info_from_dict,
    uplink_info_to_dict,
)
from unifi_topology.model.topology import PortInfo, UplinkInfo


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
        port = port_info_from_dict({"port_idx": 5})
        assert port.port_idx == 5
        assert port.name is None
        assert port.port_poe is False
        assert port.tagged_vlans == ()


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
        restored = uplink_info_from_dict(uplink_info_to_dict(uplink))
        assert restored.mac is None
