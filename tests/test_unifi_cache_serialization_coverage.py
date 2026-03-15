"""Cache serialization coverage for unifi.py."""

from __future__ import annotations

from unifi_topology.adapters import unifi


def test_device_lldp_value_prefers_lldp_info():
    assert unifi._device_lldp_value({"lldp_info": [{"chassis_id": "aa"}], "lldp": "ignored"}) == [
        {"chassis_id": "aa"}
    ]


def test_device_lldp_value_falls_back_to_lldp():
    assert unifi._device_lldp_value({"lldp": [{"chassis_id": "bb"}]}) == [{"chassis_id": "bb"}]


def test_device_lldp_value_falls_back_to_lldp_table():
    assert unifi._device_lldp_value({"lldp_table": [{"chassis_id": "cc"}]}) == [
        {"chassis_id": "cc"}
    ]


def test_device_lldp_value_returns_none_when_all_missing():
    assert unifi._device_lldp_value({}) is None


def test_serialize_network_for_cache():
    result = unifi._serialize_network_for_cache(
        {
            "_id": "net1",
            "name": "LAN",
            "vlan": 10,
            "vlan_enabled": True,
            "purpose": "corporate",
            "enabled": True,
        }
    )
    assert result["_id"] == "net1"
    assert result["name"] == "LAN"
    assert result["vlan"] == 10
    assert result["vlan_enabled"] is True
    assert result["purpose"] == "corporate"
    assert result["enabled"] is True


def test_serialize_network_for_cache_uses_fallback_fields():
    result = unifi._serialize_network_for_cache(
        {"id": "net2", "network_name": "IoT", "vlan_id": 20}
    )
    assert result["_id"] == "net2"
    assert result["name"] == "IoT"
    assert result["vlan"] == 20


def test_serialize_networks_for_cache():
    result = unifi._serialize_networks_for_cache(
        [
            {"_id": "n1", "name": "LAN", "vlan": 1, "purpose": "corporate"},
            {"_id": "n2", "name": "Guest", "vlan": 100, "purpose": "guest"},
        ]
    )
    assert len(result) == 2
    assert result[0]["_id"] == "n1"
    assert result[1]["_id"] == "n2"
