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


def test_serialize_device_preserves_state_and_stats():
    device = {
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Switch",
        "model": "USW-24",
        "type": "usw",
        "state": 1,
        "uptime": 86400,
        "num_sta": 5,
        "system-stats": {"cpu": "12.5", "mem": "38.2"},
        "general_temperature": 42,
        "tx_bytes": 1000,
        "rx_bytes": 2000,
        "total_max_power": 95.0,
        "stat": {"tx_bytes": 999},
    }
    result = unifi._serialize_device_for_cache(device)
    assert result["state"] == 1
    assert result["uptime"] == 86400
    assert result["num_sta"] == 5
    assert result["system-stats"] == {"cpu": "12.5", "mem": "38.2"}
    assert result["general_temperature"] == 42
    assert result["tx_bytes"] == 1000
    assert result["rx_bytes"] == 2000
    assert result["total_max_power"] == 95.0
    assert result["stat"] == {"tx_bytes": 999}


def test_is_rate_limited_detects_429():
    from unifi_topology.adapters.unifi_api import UnifiAuthError

    assert unifi._is_rate_limited(UnifiAuthError("Too Many Requests", status_code=429))
    assert not unifi._is_rate_limited(UnifiAuthError("Invalid credentials"))
