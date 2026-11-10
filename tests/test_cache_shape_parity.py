"""Raw API device records and their cache-serialized form must normalize identically."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from unifi_topology.adapters import unifi
from unifi_topology.model.device_stats_coerce import normalize_device_stats
from unifi_topology.model.topology_coerce import normalize_devices

pytestmark = pytest.mark.integration

_NETWORK_VLAN_MAP = {"net-default": 1, "net-iot": 30, "net-guest": 40}


def _raw_device() -> dict[str, object]:
    return {
        "name": "Core Switch",
        "model": "US24P250",
        "shortname": "US24P250",
        "mac": "aa:bb:cc:dd:ee:01",
        "ip": "192.168.1.2",
        "type": "usw",
        "version": "7.1.26",
        "connect_request_ip": "8.8.8.8",
        "uptime": 3600,
        "tx_bytes": 1000,
        "rx_bytes": 2000,
        "lldp_table": [],
        "uplink": {"uplink_mac": "aa:bb:cc:dd:ee:00", "uplink_remote_port": 4},
        "port_table": [
            {
                "port_idx": 1,
                "name": "Port 1",
                "speed": 1000,
                "up": True,
                "port_poe": True,
                "poe_enable": True,
                "poe_mode": "auto",
                "poe_power": "4.20",
                "native_networkconf_id": "net-iot",
                "tagged_vlan_mgmt": "block_all",
            },
            {"port_idx": 2, "native_networkconf_id": "net-default", "tagged_vlans": [30]},
            {"port_idx": 3, "native_networkconf_id": "net-default", "tagged_vlan_mgmt": "auto"},
            {
                "port_idx": 4,
                "native_networkconf_id": "net-default",
                "tagged_vlan_mgmt": "custom",
                "excluded_networkconf_ids": ["net-iot"],
            },
        ],
    }


def _cached_device() -> dict[str, object]:
    return unifi._serialize_device_for_cache(_raw_device())


def test_raw_port_resolves_native_vlan_from_networkconf_id():
    (device,) = normalize_devices([_raw_device()], _NETWORK_VLAN_MAP)
    assert [port.native_vlan for port in device.port_table] == [30, 1, 1, 1]


def test_trunk_modes_resolve_tagged_vlans_from_known_networks():
    (device,) = normalize_devices([_raw_device()], _NETWORK_VLAN_MAP)
    tagged = {port.port_idx: port.tagged_vlans for port in device.port_table}
    assert tagged == {1: (), 2: (30,), 3: (30, 40), 4: (40,)}


def test_raw_and_cached_devices_normalize_identically():
    # Device uses identity equality, so compare field values.
    (raw,) = normalize_devices([_raw_device()], _NETWORK_VLAN_MAP)
    (cached,) = normalize_devices([_cached_device()], _NETWORK_VLAN_MAP)
    assert asdict(raw) == asdict(cached)


def test_cached_device_keeps_public_ip_and_model_display_name():
    (device,) = normalize_devices([_cached_device()], _NETWORK_VLAN_MAP)
    assert device.public_ip == "8.8.8.8"
    assert device.model_name == "US24P250"


def test_raw_and_cached_device_stats_normalize_identically():
    assert normalize_device_stats([_cached_device()]) == normalize_device_stats([_raw_device()])


def test_cached_device_omits_absent_fields():
    cached = unifi._serialize_device_for_cache({"mac": "aa:bb:cc:dd:ee:02", "port_table": [{}]})
    assert "name" not in cached
    assert cached["port_table"] == [{}]
