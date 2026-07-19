"""Tests for classify device-path helpers."""

from types import SimpleNamespace

from unifi_topology.model._classify_device import _classify_by_device_name
from unifi_topology.model.classify import classify_device_type


def test_classify_by_device_name_returns_none_for_unknown():
    assert _classify_by_device_name("My Server") is None
    assert _classify_by_device_name("NAS") is None
    assert _classify_by_device_name("Printer") is None


def test_classify_device_type_ux_default_gateway():
    device = SimpleNamespace(type="ux")
    assert classify_device_type(device) == "gateway"


def test_classify_device_type_ux_in_gateway_mode_false():
    device = SimpleNamespace(type="ux", in_gateway_mode=False)
    assert classify_device_type(device) == "ap"


def test_classify_device_type_ux_in_gateway_mode_true():
    device = SimpleNamespace(type="ux", in_gateway_mode=True)
    assert classify_device_type(device) == "gateway"
