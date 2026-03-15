import pytest

from unifi_topology.adapters import unifi

pytestmark = pytest.mark.integration


def test_serialize_lldp_entries_filters_missing_fields():
    class Entry:
        def __init__(self, chassis_id=None, port_id=None):
            self.chassis_id = chassis_id
            self.port_id = port_id

    entries = [Entry(chassis_id="aa", port_id="1"), Entry(chassis_id="bb")]
    serialized = unifi._serialize_lldp_entries(entries)
    assert len(serialized) == 1
    assert serialized[0]["chassis_id"] == "aa"


def test_serialize_lldp_entries_accepts_single_object():
    serialized = unifi._serialize_lldp_entries({"chassis_id": "aa", "port_id": "1"})
    assert serialized[0]["port_id"] == "1"


def test_serialize_uplink_returns_none_when_empty():
    assert unifi._serialize_uplink({"uplink_mac": None, "uplink_device_name": None}) is None


def test_serialize_uplink_reads_fallback_fields():
    data = unifi._serialize_uplink(
        {"uplink_device_mac": "aa", "uplink_name": "Core", "port_idx": 3}
    )
    assert data == {"uplink_mac": "aa", "uplink_device_name": "Core", "uplink_remote_port": 3}


def test_serialize_port_entry_reads_aggregation_group():
    data = unifi._serialize_port_entry({"port_idx": 1, "agg_id": "agg2"})
    assert data["aggregation_group"] == "agg2"


def test_is_rate_limited_detects_429():
    assert unifi._is_rate_limited(Exception("HTTP 429 Too Many Requests"))
    assert not unifi._is_rate_limited(Exception("Invalid credentials"))
