"""Compatibility-focused topology tests for client and helper paths."""

from __future__ import annotations

from types import SimpleNamespace

from unifi_topology.model.classify import (
    _client_unifi_flag,
    classify_device_type,
    client_display_name,
)
from unifi_topology.model.clients import (
    _client_channel,
    build_client_edges,
    build_client_port_map,
    build_node_type_map,
    client_uplink_mac,
    client_uplink_port,
)
from unifi_topology.model.helpers import get_field
from unifi_topology.model.topology import Device


def test_client_uplink_mac_nested():
    assert client_uplink_mac({"uplink": {"uplink_mac": "aa:bb"}}) == "aa:bb"


def test_client_uplink_port_nested_str():
    assert client_uplink_port({"uplink": {"uplink_remote_port": "3"}}) == 3


def test_build_client_edges_skips_unwired():
    assert build_client_edges([{"name": "Client", "is_wired": False, "sw_mac": "aa"}], {"aa": "Switch"}) == []


def test_client_field_attribute_fallback():
    assert get_field(SimpleNamespace(name="Client"), "name") == "Client"


def test_client_display_name_missing_returns_none():
    assert client_display_name({"name": " ", "hostname": "", "mac": ""}) is None


def test_client_uplink_port_direct_int():
    assert client_uplink_port({"uplink_remote_port": 4}) == 4


def test_client_uplink_port_direct_str_digit():
    assert client_uplink_port({"sw_port": "7"}) == 7


def test_client_uplink_port_parses_port_label():
    assert client_uplink_port({"uplink_remote_port": "Port 9"}) == 9


def test_client_uplink_port_nested_int():
    assert client_uplink_port({"uplink": {"uplink_remote_port": 8}}) == 8


def test_client_uplink_mac_nested_empty():
    assert client_uplink_mac({"uplink": {"uplink_mac": ""}}) is None


def test_build_client_edges_include_ports_without_port():
    edges = build_client_edges(
        [{"name": "Client", "is_wired": True, "sw_mac": "aa"}],
        {"aa": "Switch"},
        include_ports=True,
    )
    assert edges[0].label is None


def test_build_node_type_map_skips_unwired_clients():
    assert "Client" not in build_node_type_map([], [{"name": "Client", "is_wired": False}])


def test_build_client_edges_missing_name_or_uplink():
    assert build_client_edges([{"name": "", "is_wired": True}], {"aa": "Switch"}) == []


def test_build_client_edges_dedupes():
    clients = [
        {"name": "Client", "is_wired": True, "sw_mac": "aa"},
        {"name": "Client", "is_wired": True, "sw_mac": "aa"},
    ]
    assert len(build_client_edges(clients, {"aa": "Switch"})) == 1


def test_build_node_type_map_adds_wired_client():
    node_types = build_node_type_map([], [{"name": "Client", "is_wired": True}])
    assert node_types["Client"] == "client"


def test_classify_device_type_other():
    assert classify_device_type(SimpleNamespace(type="camera")) == "other"


def test_client_unifi_flag_reads_int():
    assert _client_unifi_flag({"is_unifi": 1}) is True


def test_client_channel_reads_string():
    assert _client_channel({"wifi_channel": "36"}) == 36


def test_build_client_port_map_skips_unknown_device():
    devices = [
        Device(name="Switch", model_name="", model="", mac="aa", ip="", type="usw", lldp_info=[])
    ]
    clients = [{"name": "Client", "is_wired": True, "sw_mac": "cc", "sw_port": 3}]
    assert build_client_port_map(devices, clients, client_mode="wired") == {}


def test_classify_device_type_from_name():
    assert classify_device_type(SimpleNamespace(type="", name="Gateway Main")) == "gateway"
