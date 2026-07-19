"""Compatibility-focused topology tests for low-level client helpers."""

from __future__ import annotations

from types import SimpleNamespace

from unifi_topology.model._classify_client import _client_unifi_flag
from unifi_topology.model.classify import classify_device_type, client_display_name
from unifi_topology.model.clients import _client_channel, client_uplink_mac, client_uplink_port
from unifi_topology.model.helpers import get_field


def test_client_uplink_mac_nested():
    assert client_uplink_mac({"uplink": {"uplink_mac": "aa:bb"}}) == "aa:bb"


def test_client_uplink_port_nested_str():
    assert client_uplink_port({"uplink": {"uplink_remote_port": "3"}}) == 3


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


def test_classify_device_type_other():
    assert classify_device_type(SimpleNamespace(type="camera")) == "other"


def test_client_unifi_flag_reads_int():
    assert _client_unifi_flag({"is_unifi": 1}) is True


def test_client_channel_reads_string():
    assert _client_channel({"wifi_channel": "36"}) == 36


def test_classify_device_type_from_name():
    assert classify_device_type(SimpleNamespace(type="", name="Gateway Main")) == "gateway"
