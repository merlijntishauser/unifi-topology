"""Tests for generic snapshot value serialization."""

from __future__ import annotations

from unifi_topology.model.lldp import LLDPEntry
from unifi_topology.model.snapshot import _serialize_value
from unifi_topology.model.topology import UplinkInfo


class TestSerializeValue:
    def test_list_serialization(self):
        assert _serialize_value([1, "two", None]) == [1, "two", None]

    def test_dict_serialization(self):
        assert _serialize_value({"a": 1, "b": "two"}) == {"a": 1, "b": "two"}

    def test_nested_dataclass_serialization(self):
        uplink = UplinkInfo(mac="aa:bb:cc:dd:ee:ff", name="Switch", port=24)
        assert _serialize_value(uplink) == {
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "Switch",
            "port": 24,
        }

    def test_fallback_to_str(self):
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
        result = _serialize_value({"uplink": UplinkInfo(mac="aa:bb", name="S", port=1)})
        assert result["uplink"]["mac"] == "aa:bb"
